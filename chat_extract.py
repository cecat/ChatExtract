#!/usr/bin/env python3
"""
ChatExtract - Extract chat sessions from OpenAI data exports by date.

This tool helps you:
1. List all unique dates with conversation counts
2. Extract all conversations from a specific date to organized output folders
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict
import html
import re


def load_conversations(data_folder: Path) -> tuple[List[Dict[str, Any]], Path]:
    """Load conversations from the OpenAI export folder."""
    conversations_file = data_folder / 'conversations.json'
    chat_html_file = data_folder / 'chat.html'
    
    try:
        with open(conversations_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        conversations = data if isinstance(data, list) else []
        return conversations, chat_html_file
    except FileNotFoundError:
        print(f"Error: File not found: {conversations_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file: {e}", file=sys.stderr)
        sys.exit(1)


def format_timestamp(timestamp: float) -> str:
    """Convert Unix timestamp to readable date string."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def get_date_only(timestamp: float) -> str:
    """Convert Unix timestamp to date only (YYYY-MM-DD)."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')


def clean_openai_markup(text: str) -> str:
    """Remove OpenAI's internal citation and entity markup characters."""
    # Remove citation markers like 【cite】turn0search5【turn0search0】
    text = re.sub(r'\ue200cite\ue202[^\ue201]+\ue201', '', text)
    
    # Remove entity markers like 【entity】["software", "ChatGPT", 0]【】
    text = re.sub(r'\ue200entity\ue202\[[^\]]+\]\ue201', '', text)
    
    # Remove any remaining private use area characters (U+E000 to U+F8FF)
    text = re.sub(r'[\ue000-\uf8ff]', '', text)
    
    return text


def simple_markdown_to_html(text: str) -> str:
    """Convert basic markdown to HTML for better readability."""
    # Clean OpenAI markup first
    text = clean_openai_markup(text)
    
    # Escape HTML
    text = html.escape(text)
    
    # Headers
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    
    # Code blocks
    text = re.sub(r'```([\s\S]+?)```', r'<pre><code>\1</code></pre>', text)
    
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    
    # Line breaks - convert double newlines to paragraphs
    paragraphs = text.split('\n\n')
    formatted_paras = []
    for p in paragraphs:
        if not p.startswith('<'):
            p_with_breaks = p.replace('\n', '<br>')
            formatted_paras.append(f'<p>{p_with_breaks}</p>')
        else:
            formatted_paras.append(p)
    text = ''.join(formatted_paras)
    
    return text


def generate_html(conversations: List[Dict[str, Any]], output_file: Path) -> None:
    """Generate an HTML file from conversations for easy reading."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Extracted Conversations</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .conversation {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .conversation-header {{
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .conversation-title {{
            font-size: 24px;
            font-weight: 600;
            color: #333;
            margin: 0 0 5px 0;
        }}
        .conversation-date {{
            color: #666;
            font-size: 14px;
        }}
        .message {{
            margin: 20px 0;
            padding: 20px 24px;
            border-radius: 8px;
        }}
        .message.user {{
            background-color: #f7f7f8;
        }}
        .message.assistant {{
            background-color: transparent;
        }}
        .message.system {{
            background-color: #fff3cd;
            font-style: italic;
        }}
        .message-role {{
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            color: #6e6e80;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        }}
        .message-content {{
            color: #353740;
            line-height: 1.75;
        }}
        .message-content p {{
            margin: 0 0 1em 0;
        }}
        .message-content p:last-child {{
            margin-bottom: 0;
        }}
        .message-content h1, .message-content h2, .message-content h3 {{
            margin: 1.5em 0 0.75em 0;
            color: #202123;
        }}
        .message-content h1:first-child,
        .message-content h2:first-child,
        .message-content h3:first-child {{
            margin-top: 0;
        }}
        .message-content code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .message-content pre {{
            background: #f4f4f4;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 1em 0;
        }}
        .message-content pre code {{
            background: none;
            padding: 0;
        }}
        .message-content strong {{
            font-weight: 600;
            color: #202123;
        }}
        .message-content a {{
            color: #10a37f;
            text-decoration: none;
        }}
        .message-content a:hover {{
            text-decoration: underline;
        }}
        .summary {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .toc {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .toc h2 {{
            margin-top: 0;
            color: #333;
        }}
        .toc-list {{
            list-style: none;
            padding: 0;
        }}
        .toc-item {{
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .toc-item:last-child {{
            border-bottom: none;
        }}
        .toc-link {{
            text-decoration: none;
            color: #1976d2;
            font-weight: 500;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .toc-link:hover {{
            color: #1565c0;
            text-decoration: underline;
        }}
        .toc-time {{
            color: #666;
            font-size: 14px;
            font-weight: normal;
        }}
    </style>
</head>
<body>
    <div class="summary">
        <h1>Extracted Conversations</h1>
        <p><strong>Total conversations:</strong> {len(conversations)}</p>
    </div>
    
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul class="toc-list">
"""
    
    # Generate table of contents
    for idx, conv in enumerate(conversations, 1):
        title = html.escape(conv.get('title', 'Untitled'))
        create_time = conv.get('create_time', 0)
        time_str = format_timestamp(create_time) if create_time else 'Unknown'
        conv_id = f"conv-{idx}"
        
        html_content += f"""
            <li class="toc-item">
                <a href="#{conv_id}" class="toc-link">
                    <span>{idx}. {title}</span>
                    <span class="toc-time">{time_str}</span>
                </a>
            </li>
"""
    
    html_content += """
        </ul>
    </div>
"""
    
    # Generate conversations
    for idx, conv in enumerate(conversations, 1):
        title = html.escape(conv.get('title', 'Untitled'))
        create_time = conv.get('create_time', 0)
        date_str = format_timestamp(create_time) if create_time else 'Unknown date'
        conv_id = f"conv-{idx}"
        
        html_content += f"""
    <div class="conversation" id="{conv_id}">
        <div class="conversation-header">
            <h2 class="conversation-title">{idx}. {title}</h2>
            <div class="conversation-date">{date_str}</div>
        </div>
"""
        
        # Extract messages from mapping
        mapping = conv.get('mapping', {})
        messages = []
        
        # Build message tree and extract in order
        for node_id, node in mapping.items():
            message = node.get('message')
            if message and message.get('content'):
                author = message.get('author', {}).get('role', 'unknown')
                content = message.get('content', {})
                
                if content.get('content_type') == 'text':
                    parts = content.get('parts', [])
                    if parts:
                        text = ''.join([str(p) for p in parts if p])
                        if text.strip():
                            messages.append({
                                'role': author,
                                'content': text,
                                'create_time': message.get('create_time', 0)
                            })
        
        # Sort messages by creation time
        messages.sort(key=lambda m: m['create_time'])
        
        # Render messages with markdown
        for msg in messages:
            role = msg['role']
            content_html = simple_markdown_to_html(msg['content'])
            role_class = role if role in ['user', 'assistant', 'system'] else 'system'
            role_display = html.escape(role).upper()
            
            html_content += f"""
        <div class="message {role_class}">
            <div class="message-role">{role_display}</div>
            <div class="message-content">{content_html}</div>
        </div>
"""
        
        html_content += "    </div>\n"
    
    html_content += """
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)


def list_dates(conversations: List[Dict[str, Any]]) -> None:
    """Display all unique dates with conversation counts."""
    if not conversations:
        print("No conversations found in the export folder.")
        return
    
    # Group conversations by date
    dates = defaultdict(list)
    for conv in conversations:
        timestamp = conv.get('create_time', 0)
        if timestamp:
            date_str = get_date_only(timestamp)
            dates[date_str].append(conv)
    
    # Sort and display
    sorted_dates = sorted(dates.keys())
    print(f"\nFound {len(conversations)} conversation(s) across {len(sorted_dates)} date(s):\n")
    print(f"{'Date':<15} {'Count':<10} {'Sample Titles'}")
    print("-" * 80)
    
    for date in sorted_dates:
        convs = dates[date]
        sample_titles = ', '.join([c.get('title', 'Untitled')[:30] for c in convs[:2]])
        if len(convs) > 2:
            sample_titles += '...'
        print(f"{date:<15} {len(convs):<10} {sample_titles}")


def extract_by_date(conversations: List[Dict[str, Any]], target_date: str, 
                    data_folder: Path, chat_html_file: Path, keyword: str = None) -> None:
    """Extract all conversations from a specific date, optionally filtered by keyword."""
    # Filter conversations by date
    matching_convs = []
    for conv in conversations:
        timestamp = conv.get('create_time', 0)
        if timestamp and get_date_only(timestamp) == target_date:
            # Apply keyword filter if provided
            if keyword:
                title = conv.get('title', '').lower()
                if keyword.lower() in title:
                    matching_convs.append(conv)
            else:
                matching_convs.append(conv)
    
    if not matching_convs:
        if keyword:
            print(f"No conversations found for date: {target_date} with keyword: '{keyword}'")
        else:
            print(f"No conversations found for date: {target_date}")
        sys.exit(1)
    
    # Create output folder structure
    data_folder_name = data_folder.name
    output_folder = Path('extracted') / data_folder_name
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Write conversations.json
    output_json = output_folder / 'conversations.json'
    try:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(matching_convs, f, indent=2, ensure_ascii=False)
        
        filter_msg = f" with keyword '{keyword}'" if keyword else ""
        print(f"\nExtracted {len(matching_convs)} conversation(s) for {target_date}{filter_msg}")
        print(f"Output: {output_json}")
    except IOError as e:
        print(f"Error writing JSON file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Generate HTML file from filtered conversations
    output_html = output_folder / 'chat.html'
    try:
        generate_html(matching_convs, output_html)
        print(f"Generated: {output_html}")
    except Exception as e:
        print(f"Warning: Could not generate HTML: {e}", file=sys.stderr)
    
    # Print summary
    print(f"\nSummary:")
    for idx, conv in enumerate(matching_convs, 1):
        title = conv.get('title', 'Untitled')
        timestamp = conv.get('create_time', 0)
        time_str = format_timestamp(timestamp) if timestamp else 'Unknown'
        print(f"  {idx}. [{time_str}] {title}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract chat sessions from OpenAI data exports by date.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all dates with conversation counts
  python chat_extract.py data/Charlie-1
  
  # Extract all conversations from a specific date
  python chat_extract.py data/Charlie-1 -d 2025-10-21
  
  # Extract conversations from a date with keyword filter
  python chat_extract.py data/Charlie-1 -d 2025-10-21 -k "python"
        """
    )
    
    parser.add_argument(
        'data_folder',
        type=Path,
        help='Path to the data folder containing OpenAI export (e.g., data/Charlie-1)'
    )
    
    parser.add_argument(
        '-d', '--date',
        type=str,
        metavar='YYYY-MM-DD',
        help='Extract all conversations from this date'
    )
    
    parser.add_argument(
        '-k', '--keyword',
        type=str,
        metavar='KEYWORD',
        help='Filter conversations by keyword in title (case-insensitive)'
    )
    
    args = parser.parse_args()
    
    # Validate data folder
    if not args.data_folder.is_dir():
        parser.error(f"Data folder does not exist: {args.data_folder}")
    
    # Validate that keyword is only used with date
    if args.keyword and not args.date:
        parser.error("--keyword can only be used with --date")
    
    # Load conversations
    conversations, chat_html_file = load_conversations(args.data_folder)
    
    # List or extract
    if args.date:
        extract_by_date(conversations, args.date, args.data_folder, chat_html_file, args.keyword)
    else:
        list_dates(conversations)


if __name__ == '__main__':
    main()
