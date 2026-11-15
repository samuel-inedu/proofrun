"""A fake model for research questions. It answers 1 question correctly and 1 incorrectly."""
import sys

prompt = sys.stdin.read()
if "IPv6" in prompt:
    print("An IPv6 address is 128 bits long.\nANSWER: 128 bits")
elif "Nigeria" in prompt:
    print("ANSWER: 1 October 1963")
else:
    print("I am not sure.")
