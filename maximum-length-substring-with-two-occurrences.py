class Solution:
    def maximumLengthSubstring(self, s: str) -> int:
        frequencies = defaultdict(int)
        left = 0
        result = 0

        for right, character in enumerate(s):
            frequencies[character] += 1
            while frequencies[character] > 2:
                frequencies[s[left]] -= 1
                left += 1

            result = max(result, right - left + 1)

        return result
