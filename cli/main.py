import sys
from core.parser import parse_query
from core.search import search_files


def main():
    if len(sys.argv) < 2:
        print("Usage: seekr <query>")
        return

    query = " ".join(sys.argv[1:])

    parsed = parse_query(query)
    results = search_files(parsed)

    if not results:
        print("No files found")
        return

    print("\nResults:\n")
    for r in results[:10]:
        print(r)


if __name__ == "__main__":
    main()