import os
import argparse
import sys


def find_report_files(directory, keyword="作業日報"):
    """
    指定されたディレクトリを再帰的に走査し、ファイル名に特定のキーワードを含むファイルを見つける

    Args:
        directory (str): 検索を開始するディレクトリのパス
        keyword (str): ファイル名に含まれるキーワード

    Returns:
        list: 見つかったファイルのパスのリスト
    """
    found_files = []

    try:
        for root, _, files in os.walk(directory):
            for file in files:
                if keyword in file:
                    found_files.append(os.path.join(root, file))
    except Exception as e:
        print(f"エラー: ディレクトリの走査中に問題が発生しました: {e}", file=sys.stderr)

    return found_files


def read_file_contents(file_path):
    """
    ファイルの内容を読み込む

    Args:
        file_path (str): 読み込むファイルのパス

    Returns:
        str: ファイルの内容、またはエラーメッセージ
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        try:
            # UTF-8でエラーが出た場合はShift-JISを試す
            with open(file_path, 'r', encoding='shift_jis') as file:
                return file.read()
        except Exception as e:
            return f"エラー: ファイルの読み込みに失敗しました: {e}"
    except Exception as e:
        return f"エラー: ファイルの読み込みに失敗しました: {e}"


def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='ディレクトリ内の「作業日報」を含むファイル名を検索し内容を表示します')
    parser.add_argument('--directory', '-d', required=True, help='検索を開始するディレクトリのパス')
    args = parser.parse_args()

    # 指定されたディレクトリが存在するか確認
    if not os.path.isdir(args.directory):
        print(f"エラー: 指定されたディレクトリ '{args.directory}' は存在しないか、ディレクトリではありません", file=sys.stderr)
        sys.exit(1)

    # 「作業日報」を含むファイルを検索
    report_files = find_report_files(args.directory)

    if not report_files:
        print(f"'{args.directory}' ディレクトリ内に「作業日報」を含むファイルは見つかりませんでした。")
        sys.exit(0)

    print(f"見つかったファイル数: {len(report_files)}\n")

    # 各ファイルの内容を読み込んで表示
    for i, file_path in enumerate(report_files, 1):
        print(f"ファイル {i}/{len(report_files)}: {file_path}")
        print("-" * 80)
        content = read_file_contents(file_path)
        print(content)
        print("=" * 80)
        print()


if __name__ == "__main__":
    main()
