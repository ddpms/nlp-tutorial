# code by Tae Hwan Jung(Jeff Jung) @graykode
import numpy as np
import torch
import torch.nn as nn


# TODO: LINE BY LINE CHECK - TENSOR DIMENSIONS (ESPECIALLY OF enc_hidden and enc_states)


dtype = torch.FloatTensor
# S: Symbol that shows starting of decoding input
# E: Symbol that shows starting of decoding output
# P: Symbol that will fill in blank sequence if current batch data size is short than time steps

char_arr = [c for c in 'SEPabcdefghijklmnopqrstuvwxyz']
num_dic = {n: i for i, n in enumerate(char_arr)}

seq_data = [['man', 'women'], ['black', 'white'], ['king', 'queen'], ['girl', 'boy'], ['up', 'down'], ['high', 'low']]

# Seq2Seq Parameter
n_step = 5
n_hidden = 128
n_class = len(num_dic)
batch_size = len(seq_data)

def make_batch(seq_data):
    """
    (EXAMPLE)
    input: [10, 11, 9, 10, 2]
    decoder_input: [0, 14, 17, 25, 2, 2]
    target: [14, 17, 25, 2, 2, 1]
    input_str: ['h', 'i', 'g', 'h', 'P']
    decoder_input_str: ['S', 'l', 'o', 'w', 'P', 'P']
    target_str: ['l', 'o', 'w', 'P', 'P', 'E']
    """

    input_batch, decoder_input_batch, target_batch = [], [], []

    for seq in seq_data:
        for i in range(2):
            seq[i] = seq[i] + 'P' * (n_step - len(seq[i]))

        input = [num_dic[n] for n in seq[0]]
        decoder_input = [num_dic[n] for n in ('S' + seq[1])]
        target = [num_dic[n] for n in (seq[1] + 'E')]

        input_str = [n for n in seq[0]]
        decoder_input_str = [n for n in ('S' + seq[1])]
        target_str = [n for n in (seq[1] + 'E')]

        print("*"*30)
        print("input:", input)
        print("decoder_input:", decoder_input)
        print("target:", target)
        print("input_str:", input_str)
        print("decoder_input_str:", decoder_input_str)
        print("target_str:", target_str)
        print("*"*30)

        input_batch.append(np.eye(n_class)[input])
        decoder_input_batch.append(np.eye(n_class)[decoder_input])
        target_batch.append(target) # not one-hot


    # make tensor
    return torch.Tensor(input_batch), torch.Tensor(decoder_input_batch), torch.LongTensor(target_batch)

# Model
class Seq2Seq(nn.Module):
    def __init__(self):
        super(Seq2Seq, self).__init__()

        self.enc_cell = nn.RNN(input_size=n_class, hidden_size=n_hidden)
        self.dec_cell = nn.RNN(input_size=n_class, hidden_size=n_hidden)
        self.fc = nn.Linear(n_hidden, n_class)
        self.drop_out = nn.Dropout(0.5)

    def forward(self, enc_input, enc_hidden, dec_input):
        enc_input = enc_input.transpose(0, 1) # enc_input: [max_len(=n_step, time step), batch_size, n_class]
        dec_input = dec_input.transpose(0, 1) # dec_input: [max_len(=n_step, time step), batch_size, n_class]

        # enc_states : [num_layers(=1) * num_directions(=1), batch_size, n_hidden]
        _, enc_states = self.enc_cell(enc_input, enc_hidden)
        enc_states = self.drop_out(enc_states)

        # outputs : [max_len+1(=6), batch_size, num_directions(=1) * n_hidden(=128)]
        outputs, _ = self.dec_cell(dec_input, enc_states)
        outputs = self.drop_out(outputs)

        model = self.fc(outputs) # model : [max_len+1(=6), batch_size, n_class]
        return model


input_batch, decoder_input_batch, target_batch = make_batch(seq_data)

model = Seq2Seq()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

for epoch in range(5000):
    # make hidden shape [num_layers * num_directions, batch_size, n_hidden]
    enc_hidden = torch.zeros(1, batch_size, n_hidden)

    optimizer.zero_grad()
    # input_batch : [batch_size, max_len(=n_step, time step), n_class]
    # decoder_input_batch : [batch_size, max_len+1(=n_step, time step) (becase of 'S' or 'E'), n_class]
    # target_batch : [batch_size, max_len+1(=n_step, time step)], not one-hot
    output = model(input_batch, enc_hidden, decoder_input_batch)
    # output : [max_len+1, batch_size, n_class]
    output = output.transpose(0, 1) # [batch_size, max_len+1(=6), n_class]

    loss = 0
    for i in range(0, len(target_batch)):
        # output[i] : [max_len+1, n_class, target_batch[i] : max_len+1]
        loss += criterion(output[i], target_batch[i])

    if (epoch + 1) % 1000 == 0:
        print('Epoch:', '%04d' % (epoch + 1), 'cost =', '{:.6f}'.format(loss))

    loss.backward()
    optimizer.step()


# Test
def translate(word):

    # It is much important to note that the blank symbol 'P' is used to PAD the decoder input. Some other tricks may be possible. It is wonderful that the trick with black symbol works well.

    """
    (EXAMPLE)
    mans -> women

    input: [15, 3, 16, 21, 2]
    decoder_input: [0, 2, 2, 2, 2, 2]
    target: [2, 2, 2, 2, 2, 1]
    input_str: ['m', 'a', 'n', 's', 'P']
    decoder_input_str: ['S', 'P', 'P', 'P', 'P', 'P']
    target_str: ['P', 'P', 'P', 'P', 'P', 'E']
    """

    input_batch, decoder_input_batch, _ = make_batch([[word, 'P' * len(word)]])

    # make hidden shape [num_layers * num_directions, batch_size, n_hidden]
    enc_hidden = torch.zeros(1, 1, n_hidden)
    output = model(input_batch, enc_hidden, decoder_input_batch)
    # output : [max_len+1(=6), batch_size(=1), n_class]

    predict = output.data.max(2, keepdim=True)[1] # select n_class dimension
    decoded = [char_arr[i] for i in predict]
    end = decoded.index('E')
    translated = ''.join(decoded[:end])

    return translated.replace('P', '')

print('\n'*10)
print('(TESTING)')
print('man ->', translate('man'))
print('(TESTING)')
print('mans ->', translate('mans'))
print('(TESTING)')
print('king ->', translate('king'))
print('(TESTING)')
print('black ->', translate('black'))
print('(TESTING)')
print('upp ->', translate('upp'))