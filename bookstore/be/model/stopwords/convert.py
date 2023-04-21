import os

stopwords_files = ["baidu_stopwords.txt", "cn_stopwords.txt", "hit_stopwords.txt", "scu_stopwords.txt"]

if __name__ == "__main__":
    stop_words = set()
    this_path = os.path.dirname(os.path.abspath(__file__))
    for file in stopwords_files:
        with open(os.path.join(this_path, file), "r", encoding="utf-8") as f:
            words = [word.strip() for word in f.readlines()]
            stop_words.update(set(words))
    stop_words = list(stop_words)
    for i, word in enumerate(stop_words):
        if word == '\"':
            stop_words[i] = "\\\""
    with open(os.path.join(os.path.dirname(this_path), "stopwords.py"), "w", encoding="utf-8") as f:
        f.writelines('stopwords = [\"' + '\", \"'.join(stop_words) + '\"]')
