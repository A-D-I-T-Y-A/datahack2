from keras.preprocessing.text import Tokenizer
from DataReader import DataReader
from nltk.corpus import stopwords
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers.wrappers import Bidirectional
from keras.layers import Embedding
import numpy as np
from keras.preprocessing.sequence import pad_sequences
from gensim.models.keyedvectors import KeyedVectors
import file_paths
import math

# This is our BLSTM module. It starts off by first reading in the tweet and labels file.
# It then tokenizes the data, followed up by encoding the documents into sequences of numbers and weight
# matrix construction. Lastly, it initializes the Embedding Layer and BLSTM layer for training and prediction


def get_tweets_labels(tweet_file, labels_file,tests_file):
#Simply read in data
    data_reader = DataReader(tweet_file, labels_file,tests_file)
    tweets = data_reader.read_tweets()
    labels = data_reader.read_labels()
    tests = data_reader.read_tests()
    return tweets, labels, tests


def smoothen_tweets(tweets):
#Tokenization
    stops = set(stopwords.words("english"))
    smoothened_tweets = []
    for tweet in tweets:
        words = tweet.split(" ")
        str = ""
        for word in words:
            if word[0] != "@" and word not in stops:
                if word[0] == "#":
                    word = word[1:]
                str += word + " "
        smoothened_tweets.append(str)
    return smoothened_tweets


def encode_docs(tweets):
    #Translate tweets to sequence of numbers
    tokenizer = Tokenizer(filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n', split=" ", lower=True)
    tokenizer.fit_on_texts(tweets)
    return tokenizer, tokenizer.texts_to_sequences(tweets)


def format_train(encoded_docs, labels, max_length, train_range):
    #Apply padding to data set and convert labels to bit vector form
    Xtrain = pad_sequences(encoded_docs[:70000], maxlen=max_length, padding='post')
    Ytrain = []
    for emoji in labels[:70000]:
        num = int(emoji)
        bit_vec = np.zeros(20)
        bit_vec[num] = 1
        Ytrain.append(bit_vec)
    Ytrain = np.asarray(Ytrain)
    return Xtrain, Ytrain


def format_test(encoded_docs, labels, max_length, test_range):
    # Apply padding to data set and convert labels to bit vector form
    Xtest = pad_sequences(encoded_docs[:70000], maxlen=max_length, padding='post')
    Ytest = []
    for emoji in labels[:70000]:
        num = int(emoji)
        bit_vec = np.zeros(20)
        bit_vec[num] = 1
        Ytest.append(bit_vec)
    Ytest = np.asarray(Ytest)
    return Xtest, Ytest


def populate_weight_matrix(vocab, raw_embedding):
    # Create weight matrix from pre-trained embeddings
    vocab_size = len(vocab) + 1
    weight_matrix = np.zeros((vocab_size, 300))
    for word, i in vocab.items():
        if word in raw_embedding:
            weight_matrix[i] = raw_embedding[word]
    return weight_matrix


def form_model_and_fit(weight_matrix, vocab_size, max_length, Xtrain, Ytrain, Xtest, Ytest, tests):
    #Core model training
    embedding_layer = Embedding(vocab_size, 300, weights=[weight_matrix], input_length=max_length, trainable=True, mask_zero=True)
    model = Sequential()
    model.add(embedding_layer)
    model.add(Bidirectional(LSTM(128, dropout=0.2, return_sequences=True)))
    model.add(Bidirectional(LSTM(128, dropout=0.2)))
    model.add(Dense(20, activation='softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    model.fit(Xtrain, Ytrain, epochs=1, validation_data=(Xtest, Ytest),verbose=1)

    return model.predict(tests)


def run_LSTM(tweets, labels,tests):
    #Driver function
    #tweets, labels, tests = get_tweets_labels(tweet_file, labels_file,tests_file)
    print(len(tweets))
    print(type(tweets))
    #print(tweets[70000])
    tweets = smoothen_tweets(tweets)
    tests = smoothen_tweets(tests)
    max_length = math.ceil(sum([len(s.split(" ")) for s in tweets])/len(tweets))
    
    tokenizer, encoded_docs = encode_docs(tweets + tests)
    testtokenizer, test_encoded_docs = encode_docs(tests)
    Xtrain, Ytrain = format_train(encoded_docs, labels,max_length, 40000)
    Xtest, Ytest = format_test(encoded_docs, labels, max_length, 10000)
    tests = pad_sequences(tokenizer.texts_to_sequences(tests), maxlen=max_length, padding='post')
    print("at vocab")
    vocab = tokenizer.word_index
    raw_embedding = KeyedVectors.load_word2vec_format('model_swm_300-6-10-low.w2v', binary=False)
    print("at weightmatrix")
    weight_matrix = populate_weight_matrix(vocab, raw_embedding)
    print("training")
    preds = form_model_and_fit(weight_matrix, len(vocab) + 1, max_length, Xtrain, Ytrain, Xtest, Ytest, tests)
    return preds

#accuracy = run_LSTM(file_paths.us_tweets_path, file_paths.us_labels_path)
#print(accuracy)