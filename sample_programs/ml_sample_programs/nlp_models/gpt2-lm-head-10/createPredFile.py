import numpy as np
import glob
import os
import json
import sys
from transformers import GPT2Tokenizer
import tensorflow as tf

ROOT = os.getcwd()
LLFI_OUT = os.path.join(ROOT, 'llfi')
PROG_OUT = os.path.join(LLFI_OUT, 'prog_output')

inputs = []
inputs.append("This chair is white and the table is")
inputs.append("It is bright and")
inputs.append("I am a doctor and I work at a")
inputs.append("I like playing with my")
inputs.append("A rose by any other name would smell as")
inputs.append("US-led coalition air strikes on a jail run by the Islamic State group in eastern Syria killed")
inputs.append("A magazine supplement with an image of Adolf Hitler and the title 'The Unreadable Book' is pictured in")
inputs.append("Winter isn't done with us yet. Ottawa can expect another 10 to 15 centimetres of")
inputs.append("Refined mansion tax proposal being fed into debate on abolishing 50p tax rate for those earning more than")
inputs.append("Ghazala Khan, the mother of a fallen U.S. soldier of Muslim faith, is responding to Donald Trump’s")

tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

def lltfi_sort(elem):                                                           
    return int(elem.split('layeroutput')[-1].split('-')[-1].split('.txt')[0])

def main(inpSample):
    # Get LLTFI outputs in listResArr
    listResArr = []
    list_of_files = sorted( filter( lambda x: os.path.isfile(os.path.join(PROG_OUT, x)),
                            os.listdir(PROG_OUT) ), key=lltfi_sort )

    for i in range(len(list_of_files)):
        list_of_files[i] = os.path.join(PROG_OUT, list_of_files[i])

    for filename in list_of_files:
        resforSingleInput = []
        with open(filename, "r") as read_file:
            resultJson = json.load(read_file)

            for key, value in resultJson.items():
                resforSingleInput.append(value['Data'])
            listResArr.append(resforSingleInput)

    list_output_np = []
    # Reshape the output and store as numpy array
    for elem in listResArr:
        output_np = np.asarray(elem[0])
        output_np = output_np.reshape(1,1,-1,50257) # Shape (1,1,len,50257)
        list_output_np.append(output_np)

    tokens = np.array(tokenizer.encode(inputs[inpSample]))

    # Script to convert numpy output to text
    listPreds = []
    for elemIndex in range(len(list_output_np)):
        input_to_model = tf.convert_to_tensor(
                        [[tokenizer.encode(inputs[inpSample], add_special_tokens=True)]]) # Shape [1, 1, len]
        prev = input_to_model # [1, 1, len] Set prev as input in the first step
        prev = prev[0] # [1, len]
        output = prev
        logits = list_output_np[elemIndex][0]
        logits = logits[:, -1, :]
        logits = tf.convert_to_tensor(logits)
        log_probs = tf.nn.softmax(logits,axis=-1)
        prob, prev = tf.math.top_k(log_probs, k=10)
        output = tf.concat((output, prev), axis=1)

        final_output = output[:, len(tokens):].numpy().tolist()

        listPreds.append(f"Run #{elemIndex} Predictions and Probability:\n")
        for opNum in range(0, len(final_output[0])):
            text = tokenizer.decode(final_output[0][opNum])
            opProb = prob.numpy()[0][opNum]
            listPreds.append(f"{text} : {opProb}\n")

        myfile = open('prediction/PredResult.txt', 'w')
        myfile.writelines(listPreds)
        myfile.close()


if __name__ == "__main__":
    inpSample = int(sys.argv[1])
    main(inpSample)
