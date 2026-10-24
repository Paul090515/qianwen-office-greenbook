#!/usr/bin/env python3
"""Read-only integrity and exercise checks for a greenbook project."""
import argparse
import base64
import csv
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote_to_bytes


class HTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.images = set(), [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a":
            self.links.append(a)
        if tag == "img":
            self.images.append(a)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read_json(path):
    require(path.is_file(), f"缺少核对材料：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def embedded(html, filename):
    for a in html.links:
        if a.get("download") == filename and a.get("href", "").startswith("data:"):
            header, payload = a["href"].split(",", 1)
            return base64.b64decode(payload) if ";base64" in header else unquote_to_bytes(payload)
    raise ValueError(f"HTML 缺少内嵌下载：{filename}")


def csv_rows(path):
    require(path.is_file(), f"缺少核对材料：{path}")
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def verify_registration(root):
    rows = csv_rows(root / "practice/活动报名练习.csv")
    answer = read_json(root / "practice/核对答案.json")
    done = [r for r in rows if r["状态"] == "完成"]
    monthly, channels = {}, {}
    statuses = {r["状态"] for r in rows}
    require(statuses <= {"完成", "取消"}, f"报名 CSV 含未知状态：{sorted(statuses - {'完成', '取消'})}")
    for r in done:
        net = int(r["实收"]) - int(r["退款"])
        month = r["日期"][:7]
        monthly[month] = monthly.get(month, 0) + net
        channels[r["报名渠道"]] = channels.get(r["报名渠道"], 0) + net
    gross, refunds = sum(int(r["实收"]) for r in done), sum(int(r["退款"]) for r in done)
    net = gross - refunds
    expected = {
        "全部行数": len(rows), "取消行数": sum(r["状态"] == "取消" for r in rows),
        "实收合计": gross, "退款合计": refunds, "按月": monthly,
        "纳入记录数": len(done), "净收款": net, "按报名渠道": channels,
    }
    for key in answer:
        match = re.fullmatch(r"(\d{1,2})月环比", key)
        if match:
            month_number = int(match.group(1))
            month = date(2000, month_number, 1)
            pairs = []
            for current_key in monthly:
                current = date.fromisoformat(current_key + "-01")
                if current.month != month.month:
                    continue
                previous = date(current.year - (current.month == 1), current.month - 1 if current.month > 1 else 12, 1)
                previous_key = previous.strftime("%Y-%m")
                if previous_key in monthly:
                    pairs.append((current_key, previous_key))
            require(len(pairs) == 1, f"無法唯一复算 {key}：CSV 必须只含一组该月及其前一月的相邻月份")
            current_key, previous_key = pairs[0]
            require(monthly[previous_key] != 0, f"无法复算 {key}：前一月净收款为零")
            expected[key] = round((monthly[current_key] / monthly[previous_key] - 1) * 100, 2)
    for key, value in expected.items():
        require(answer.get(key) == value, f"报名答案不匹配：{key}；文件值={answer.get(key)!r}，复算值={value!r}")


def verify_tools(root):
    rows = csv_rows(root / "practice/工具借还练习.csv")
    answer = read_json(root / "practice/工具借还核对答案.json")
    cutoff = date.fromisoformat(answer["核对时点"][:10])
    stock, borrowed, overdue, due, not_due = [], [], [], [], []
    for r in rows:
        if not r["借出日期"] or r["实际归还日"]:
            stock.append(r["工具编号"])
        else:
            borrowed.append(r["工具编号"])
            due_date = date.fromisoformat(r["约定归还日"])
            (overdue if due_date < cutoff else due if due_date == cutoff else not_due).append(r["工具编号"])
    expected = {
        "工具总数": len(rows), "在架": {"数量": len(stock), "工具编号": stock},
        "借出": {"数量": len(borrowed), "工具编号": borrowed},
        "借出中逾期": {"数量": len(overdue), "工具编号": overdue},
        "今日到期": {"数量": len(due), "工具编号": due},
        "借出中未到期": {"数量": len(not_due), "工具编号": not_due},
    }
    for key, value in expected.items():
        require(answer.get(key) == value, f"工具答案不匹配：{key}；文件值={answer.get(key)!r}，复算值={value!r}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    root = args.project.resolve()
    manifest = read_json(root / "manifest.json")
    sections = manifest.get("sections", [])
    require(len(sections) == manifest.get("chapters"), "manifest 章节数与 sections 不一致")
    require(len(sections) == manifest.get("contentsEntries"), "manifest 目录数与 sections 不一致")
    md = root / "千问办公绿皮书.md"
    require(md.is_file(), f"缺少核对材料：{md}")
    md_text = md.read_text(encoding="utf-8")
    for section in sections:
        require((root / "chapters" / section["file"]).is_file(), f"缺少章节源文件：{section['file']}")
        require(f"#{section['id']}" in md_text, f"文稿缺少目录入口：{section['id']}")
    links = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md_text)
    for link in links:
        require((root / link).is_file(), f"文稿配图不存在：{link}")
    require(len(links) == manifest.get("figures"), "文稿图片数与 manifest 不一致")
    html_path, index_path = root / "千问办公绿皮书.html", root / "index.html"
    require(html_path.is_file() and index_path.is_file(), "缺少中文 HTML 或 index.html")
    html_bytes = html_path.read_bytes()
    require(html_bytes == index_path.read_bytes(), "中文 HTML 与 index.html 字节不一致")
    parsed = HTML()
    parsed.feed(html_bytes.decode("utf-8"))
    for section in sections:
        require(section["id"] in parsed.ids, f"HTML 缺少章节锚点：{section['id']}")
        require(any(a.get("href") == "#" + section["id"] for a in parsed.links), f"HTML 目录缺少入口：{section['id']}")
    task_links = {a.get("href", "")[1:] for a in parsed.links if a.get("href", "").startswith("#task-")}
    require(task_links == {section["id"] for section in sections}, "HTML 任务目录入口与 manifest 不一致")
    images = [image for image in parsed.images if image.get("src")]
    require(len(images) == manifest.get("figures") + 1, "HTML 正文图数量加封面图与 manifest 不符")
    for image in images:
        require(image["src"].startswith("data:image/"), f"HTML 图片未内嵌：{image.get('alt', '')}")
        try:
            require(int(image.get("width", 0)) > 0 and int(image.get("height", 0)) > 0, f"图片缺少有效宽高：{image.get('alt', '')}")
        except ValueError:
            raise ValueError(f"图片宽高不是正整数：{image.get('alt', '')}")
    # Every embedded reader download is byte-checked against its editable/source counterpart.
    downloads = {
        "千问办公绿皮书.md": md,
        "活动报名练习.csv": root / "practice/活动报名练习.csv",
        "核对答案.json": root / "practice/核对答案.json",
        "工具借还练习.csv": root / "practice/工具借还练习.csv",
        "工具借还核对答案.json": root / "practice/工具借还核对答案.json",
    }
    for name, path in downloads.items():
        require(path.is_file(), f"缺少核对材料：{path}")
        require(embedded(parsed, name) == path.read_bytes(), f"HTML 内嵌下载与源文件不一致：{name}")
    verify_registration(root)
    verify_tools(root)
    print(f"通过：{len(sections)} 章，{len(links)} 幅正文图，封面图 1 幅；目录、图片、双 HTML、5 项内嵌下载及两组练习答案均匹配。")


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"校验失败：{exc}", file=sys.stderr)
        sys.exit(1)
