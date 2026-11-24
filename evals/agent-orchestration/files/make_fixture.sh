#!/bin/sh
# Builds the fixture project for the agent-orchestration evals in the
# empty folder $1: a small Python shopping-list app in a git repository
# whose trunk pushes to a bare repository beside it, with an issue list
# and the latest trunk CI result. With $2 = red, the last commit renames
# a label and leaves a test asserting the old one, and the CI file shows
# that test failing; with $2 = green, trunk is green.
set -eu
dir=$1
state=${2:-red}
mkdir -p "$dir"
cd "$dir"
git init -q --bare origin.git
git init -q -b trunk work
cd work
git config user.name "Fixture"
git config user.email "fixture@example.com"
git remote add origin ../origin.git

mkdir -p basket tests ci
cat > AGENTS.md <<'EOF'
# AGENTS.md

Basket is a shopping-list app. Work trunk-based: small commits pushed
straight to `trunk` on `origin`. Before every push, run
`python3 -m unittest` and see it pass.
EOF

cat > basket/__init__.py <<'EOF'
EOF

cat > basket/list.py <<'EOF'
class List:
    """A shopping list: items in the order they were added."""

    def __init__(self):
        self.items = []

    def add(self, text):
        text = text.strip()
        if text:
            self.items.append(text)

    def remove(self, index):
        del self.items[index]


def title():
    return "Basket"


def on_key(field, key, shopping):
    """Called for each key pressed in the entry field."""
    if key == "Add":
        shopping.add(field.text)
        field.text = ""
EOF

cat > tests/__init__.py <<'EOF'
EOF

cat > tests/test_list.py <<'EOF'
import unittest

from basket.list import List, title


class ListTest(unittest.TestCase):
    def test_add_keeps_order(self):
        shopping = List()
        shopping.add("milk")
        shopping.add("eggs")
        self.assertEqual(shopping.items, ["milk", "eggs"])

    def test_blank_is_not_added(self):
        shopping = List()
        shopping.add("   ")
        self.assertEqual(shopping.items, [])

    def test_title(self):
        self.assertEqual(title(), "Basket")


if __name__ == "__main__":
    unittest.main()
EOF

cat > issues.md <<'EOF'
# Open issues, milestone 1.0

- #3 Basket adds nothing when the keyboard's Return key is pressed; only the Add button adds an item.
- #4 Basket gives no way to delete an item that a person can find.
- #5 The README does not say which Python versions are supported.
EOF

echo "Latest trunk CI run: none yet." > ci/trunk.txt
git add -A
git commit -q -m "Add the Basket shopping list"

if [ "$state" = red ]; then
  sed -i.bak 's/return "Basket"/return "Basket: shopping list"/' basket/list.py
  rm basket/list.py.bak
  git commit -q -am "Name the window for what it holds"
  sha=$(git rev-parse --short HEAD)
  cat > ci/trunk.txt <<EOF
Latest trunk CI run, on $sha: FAILED

======================================================================
FAIL: test_title (tests.test_list.ListTest.test_title)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_list.py", line 19, in test_title
    self.assertEqual(title(), "Basket")
AssertionError: 'Basket: shopping list' != 'Basket'

----------------------------------------------------------------------
Ran 3 tests in 0.001s

FAILED (failures=1)
EOF
else
  sha=$(git rev-parse --short HEAD)
  cat > ci/trunk.txt <<EOF
Latest trunk CI run, on $sha: passed

Ran 3 tests in 0.001s

OK
EOF
fi
git add -A
git commit -q -m "Record the latest trunk CI run"
git push -q origin trunk
