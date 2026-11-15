"""A fake model. Its patch refers to a file that does not exist."""
import sys

sys.stdin.read()
print('''--- a/no/such/file.py
+++ b/no/such/file.py
@@ -1,1 +1,1 @@
-old
+new''')
