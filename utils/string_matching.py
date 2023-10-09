def levenshtein_distance(s1, s2):
    """
    Calculates the Levenshtein distance between two strings s1 and s2.
    Returns an integer representing the number of edits required to transform s1 into s2.
    """
    matrix = [[i + j for j in range(len(s2) + 1)] for i in range(len(s1) + 1)]

    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            # Calculate the cost of transforming s1[:i] into s2[:j]
            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            # Update the matrix at position (i,j) with the minimum cost of three possible operations
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,  # deletion
                matrix[i][j - 1] + 1,  # insertion
                matrix[i - 1][j - 1] + cost  # substitution or no change
            )
    return matrix[-1][-1]


def similarity_score(str1, str2):
    """
    Calculates the similarity score between two strings using the Levenshtein distance algorithm.
    Returns a float between 0.0 and 1.0, where 1.0 means the strings are identical.
    """
    distance = levenshtein_distance(str1.lower(), str2.lower())
    max_len = max(len(str1), len(str2))
    if max_len == 0:
        return 1.0  # Both strings are empty
    else:
        return 1.0 - (distance / max_len)


def similarity_score_multiple(str1, list_str2):
    best_score = 0
    for str2 in list_str2:
        score = similarity_score(str1, str2)
        if score > best_score:
            best_score = score
    return best_score


def is_substring(substring: str, string: str):
    return substring.lower() in string.lower()
