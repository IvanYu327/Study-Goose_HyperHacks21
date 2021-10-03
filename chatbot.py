import numpy as np
import tensorflow as tf
import tflearn
import random

import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

import json
import pickle
import warnings
warnings.filterwarnings("ignore")


#read intents
with open('intents.json') as json_data:
    intents = json.load(json_data)


with open("data.pickle", "rb") as f:
    words, labels, training, output = pickle.load(f)
words = []
classifyingTags = []
documents = []
stringsToIgnore = ['?,!']
print("Looping through the Intents to Convert them to words, classifyingTags, documents and stringsToIgnore.......")
for intent in intents['intents']:
    for pattern in intent['patterns']:
        # tokenize each word in the sentence
        w = nltk.word_tokenize(pattern)
        # add to our words list
        words.extend(w)
        # add to documents in our corpus
        documents.append((w, intent['tag']))
        # add to our classifyingTags list
        if intent['tag'] not in classifyingTags:
            classifyingTags.append(intent['tag'])


words = [stemmer.stem(w.lower()) for w in words if w not in stringsToIgnore]
words = sorted(list(set(words)))

# remove duplicates
classifyingTags = sorted(list(set(classifyingTags)))



training = []
output = []

output_empty = [0] * len(classifyingTags)

for doc in documents:
    # initialize our bag of words
    bag = []
    # list of tokenized words for the pattern
    pattern_words = doc[0]
    # stem each word
    pattern_words = [stemmer.stem(word.lower()) for word in pattern_words]
    # create our bag of words array
    for w in words:
        bag.append(1) if w in pattern_words else bag.append(0)

    # output is a '0' for each tag and '1' for current tag
    output_row = list(output_empty)
    output_row[classifyingTags.index(doc[1])] = 1

    training.append([bag, output_row])

random.shuffle(training)
training = np.array(training)


train_x = list(training[:,0])
train_y = list(training[:,1])

tf.compat.v1.reset_default_graph()


net = tflearn.input_data(shape=[None, len(train_x[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(train_y[0]), activation='softmax')
net = tflearn.regression(net)



model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')


model.fit(train_x, train_y, n_epoch=1000, batch_size=8, show_metric=True)

model.save('model.tflearn')



pickle.dump( {'words':words, 'classifyingTags':classifyingTags, 'train_x':train_x, 'train_y':train_y}, open( "training_data", "wb" ) )



data = pickle.load( open( "training_data", "rb" ) )
words = data['words']
classifyingTags = data['classifyingTags']
train_x = data['train_x']
train_y = data['train_y']


with open('intents.json') as json_data:
    intents = json.load(json_data)
    

# load our saved model
model.load('./model.tflearn')


def clean_up_sentence(sentence):
    # It Tokenize or Break it into the constituents parts of Sentense.
    sentence_words = nltk.word_tokenize(sentence)
    # Stemming means to find the root of the word.
    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words]
    return sentence_words

# Return the Array of Bag of Words: True or False and 0 or 1 for each word of bag that exists in the Sentence
def bow(sentence, words):
    sentence_words = clean_up_sentence(sentence)
    bag = [0]*len(words)
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s:
                bag[i] = 1
    return(np.array(bag))

def classify(sentence):
    # Prediction or To Get the Posibility or Probability from the Model
    results = model.predict([bow(sentence, words)])[0]
    # Exclude those results which are Below Threshold
    results = [[i,r] for i,r in enumerate(results) if r>0.25]
    # Sorting is Done because heigher Confidence Answer comes first.
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append((classifyingTags[r[0]], r[1])) #Tuppl -> Intent and Probability
    return return_list

def response(sentence, userID='123'):
    results = classify(sentence)
    # That Means if Classification is Done then Find the Matching Tag.
    if results:
        # Long Loop to get the Result.
        while results:
            for i in intents['intents']:
                # Tag Finding
                if i['tag'] == results[0][0]:
                    # Random Response from High Order Probabilities
                    
                    temp = random.choice(i['responses'])
                    print("RETURNING "+temp)
                    return temp

            results.pop(0)


# while True:
#     input_data = input("You- ")
#     answer = response(input_data)
#     answer

# async def chatAI(message):
    
#     print("start AI")
#     print(message)
#     responseMSG = response(message)
#     print(responseMSG)
#     return responseMSG