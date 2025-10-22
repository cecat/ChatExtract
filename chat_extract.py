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
                    data_folder: Path, chat_html_file: Path) -> None:
    """Extract all conversations from a specific date."""
    # Filter conversations by date
    matching_convs = []
    for conv in conversations:
        timestamp = conv.get('create_time', 0)
        if timestamp and get_date_only(timestamp) == target_date:
            matching_convs.append(conv)
    
    if not matching_convs:
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
        print(f"\nExtracted {len(matching_convs)} conversation(s) for {target_date}")
        print(f"Output: {output_json}")
    except IOError as e:
        print(f"Error writing JSON file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Copy chat.html if it exists
    if chat_html_file.exists():
        output_html = output_folder / 'chat.html'
        try:
            import shutil
            shutil.copy2(chat_html_file, output_html)
            print(f"Copied: {output_html}")
        except IOError as e:
            print(f"Warning: Could not copy chat.html: {e}", file=sys.stderr)
    
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
    
    args = parser.parse_args()
    
    # Validate data folder
    if not args.data_folder.is_dir():
        parser.error(f"Data folder does not exist: {args.data_folder}")
    
    # Load conversations
    conversations, chat_html_file = load_conversations(args.data_folder)
    
    # List or extract
    if args.date:
        extract_by_date(conversations, args.date, args.data_folder, chat_html_file)
    else:
        list_dates(conversations)


if __name__ == '__main__':
    main()
