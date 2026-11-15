"""A fake model. It reads the prompt and replies with the correct Python fix in a code block."""
import sys

sys.stdin.read()
print("Here is the fix.\n")
print("```diff")
print('''--- a/slugkit/slug.py
+++ b/slugkit/slug.py
@@ -3,5 +3,5 @@ import re
 
 def slugify(text, separator="-"):
     """Change text into a lowercase slug for a web address."""
-    words = re.sub(r"[^a-z0-9]", " ", text.lower()).split(" ")
+    words = re.sub(r"[^a-z0-9]", " ", text.lower()).split()
     return separator.join(words)''')
print("```")
