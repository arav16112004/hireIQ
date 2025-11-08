-- ============================================================
-- 🧪 OA SAMPLE DATA - 5 MEDIUM CODING QUESTIONS
-- ============================================================

USE DATABASE TEAM_SERO;
USE SCHEMA PUBLIC;

-- ============================================================
-- Question 1: Two Sum
-- ============================================================

INSERT INTO oa_questions (title, description, difficulty, language, time_limit, memory_limit, points, is_active, starter_code)
VALUES (
    'Two Sum',
    'Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.

Example:
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: nums[0] + nums[1] = 2 + 7 = 9

Constraints:
- 2 <= nums.length <= 10^4
- -10^9 <= nums[i] <= 10^9
- Only one valid answer exists',
    'medium',
    'python',
    5.0,
    128000,
    100,
    TRUE,
    'def two_sum(nums, target):
    # Your code here
    pass'
);

-- Test cases for Two Sum (question_id will be 1)
INSERT INTO oa_test_cases (question_id, input, expected_output, is_hidden, points)
VALUES 
    (1, '2,7,11,15
9', '0,1', FALSE, 25),
    (1, '3,2,4
6', '1,2', FALSE, 25),
    (1, '3,3
6', '0,1', FALSE, 25),
    (1, '-1,-2,-3,-4,-5
-8', '2,4', TRUE, 25);

-- ============================================================
-- Question 2: Valid Parentheses
-- ============================================================

INSERT INTO oa_questions (title, description, difficulty, language, time_limit, memory_limit, points, is_active, starter_code)
VALUES (
    'Valid Parentheses',
    'Given a string containing just the characters ''('', '')'', ''{'', ''}'', ''['' and '']'', determine if the input string is valid.

An input string is valid if:
1. Open brackets are closed by the same type of brackets.
2. Open brackets are closed in the correct order.

Example:
Input: s = "()[]{}"
Output: true

Input: s = "(]"
Output: false

Constraints:
- 1 <= s.length <= 10^4
- s consists of parentheses only ''()[]{}''',
    'medium',
    'python',
    5.0,
    128000,
    100,
    TRUE,
    'def is_valid(s):
    # Your code here
    pass'
);

-- Test cases for Valid Parentheses (question_id will be 2)
INSERT INTO oa_test_cases (question_id, input, expected_output, is_hidden, points)
VALUES 
    (2, '()', 'true', FALSE, 20),
    (2, '()[]{}', 'true', FALSE, 20),
    (2, '(]', 'false', FALSE, 20),
    (2, '([)]', 'false', TRUE, 20),
    (2, '{[]}', 'true', TRUE, 20);

-- ============================================================
-- Question 3: Longest Substring Without Repeating Characters
-- ============================================================

INSERT INTO oa_questions (title, description, difficulty, language, time_limit, memory_limit, points, is_active, starter_code)
VALUES (
    'Longest Substring Without Repeating',
    'Given a string s, find the length of the longest substring without repeating characters.

Example:
Input: s = "abcabcbb"
Output: 3
Explanation: The answer is "abc", with the length of 3.

Input: s = "bbbbb"
Output: 1
Explanation: The answer is "b", with the length of 1.

Constraints:
- 0 <= s.length <= 5 * 10^4
- s consists of English letters, digits, symbols and spaces.',
    'medium',
    'python',
    5.0,
    128000,
    100,
    TRUE,
    'def length_of_longest_substring(s):
    # Your code here
    pass'
);

-- Test cases for Longest Substring (question_id will be 3)
INSERT INTO oa_test_cases (question_id, input, expected_output, is_hidden, points)
VALUES 
    (3, 'abcabcbb', '3', FALSE, 25),
    (3, 'bbbbb', '1', FALSE, 25),
    (3, 'pwwkew', '3', FALSE, 25),
    (3, ' ', '1', TRUE, 25);

-- ============================================================
-- Question 4: Group Anagrams
-- ============================================================

INSERT INTO oa_questions (title, description, difficulty, language, time_limit, memory_limit, points, is_active, starter_code)
VALUES (
    'Group Anagrams',
    'Given an array of strings, group the anagrams together. You can return the answer in any order.

An Anagram is a word formed by rearranging the letters of a different word.

Example:
Input: strs = ["eat","tea","tan","ate","nat","bat"]
Output: [["bat"],["nat","tan"],["ate","eat","tea"]]

Constraints:
- 1 <= strs.length <= 10^4
- 0 <= strs[i].length <= 100
- strs[i] consists of lowercase English letters',
    'medium',
    'python',
    5.0,
    128000,
    100,
    TRUE,
    'def group_anagrams(strs):
    # Your code here
    # Return list of lists
    pass'
);

-- Test cases for Group Anagrams (question_id will be 4)
INSERT INTO oa_test_cases (question_id, input, expected_output, is_hidden, points)
VALUES 
    (4, 'eat,tea,tan,ate,nat,bat', '[[bat],[nat,tan],[ate,eat,tea]]', FALSE, 33),
    (4, '', '[[]]', FALSE, 33),
    (4, 'a', '[[a]]', FALSE, 34);

-- ============================================================
-- Question 5: Binary Tree Level Order Traversal
-- ============================================================

INSERT INTO oa_questions (title, description, difficulty, language, time_limit, memory_limit, points, is_active, starter_code)
VALUES (
    'Binary Tree Level Order Traversal',
    'Given the root of a binary tree, return the level order traversal of its nodes values (i.e., from left to right, level by level).

Example:
Input: root = [3,9,20,null,null,15,7]
Output: [[3],[9,20],[15,7]]

Tree representation:
    3
   / \
  9  20
    /  \
   15   7

Constraints:
- Number of nodes in the tree is in range [0, 2000]
- -1000 <= Node.val <= 1000',
    'medium',
    'python',
    5.0,
    128000,
    100,
    TRUE,
    'class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def level_order(root):
    # Your code here
    pass'
);

-- Test cases for Binary Tree Level Order (question_id will be 5)
INSERT INTO oa_test_cases (question_id, input, expected_output, is_hidden, points)
VALUES 
    (5, '3,9,20,null,null,15,7', '[[3],[9,20],[15,7]]', FALSE, 50),
    (5, '1', '[[1]]', FALSE, 25),
    (5, '', '[]', TRUE, 25);

-- ============================================================
-- Verify data inserted
-- ============================================================

SELECT COUNT(*) AS total_questions FROM oa_questions;
SELECT COUNT(*) AS total_test_cases FROM oa_test_cases;

SELECT 
    q.id,
    q.title,
    q.difficulty,
    q.language,
    COUNT(tc.id) AS test_case_count
FROM oa_questions q
LEFT JOIN oa_test_cases tc ON q.id = tc.question_id
GROUP BY q.id, q.title, q.difficulty, q.language
ORDER BY q.id;

-- ============================================================
-- ✅ Done! 5 medium questions with test cases inserted
-- ============================================================

