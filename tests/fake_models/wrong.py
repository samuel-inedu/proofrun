"""A fake model. Its patch applies, but the patch breaks a test that passed before."""
import sys

sys.stdin.read()
print('''```diff
--- a/slugkit/slug.py
+++ b/slugkit/slug.py
@@ -3,5 +3,5 @@ import re
 
 def slugify(text, separator="-"):
     """Change text into a lowercase slug for a web address."""
-    words = re.sub(r"[^a-z0-9]", " ", text.lower()).split(" ")
+    words = re.sub(r"[^a-z0-9]", " ", text.lower()).split()
-    return separator.join(words)
+    return "-".join(words)
```''')
