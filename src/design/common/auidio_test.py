# encoding= utf-8
# __author__= gary
import librosa
import librosa.display
import matplotlib.pyplot as plt

# y, sr = librosa.load('test.wav', sr=None)
# # plot a wavform
# plt.figure()
# librosa.display.waveshow(y, sr)
# plt.title('Beat wavform')
# plt.show()

# 过零率的计算
# #导入音频文件
x, sr = librosa.load('test.wav')
plt.figure(figsize=(14,5))
librosa.display.waveshow(x, sr=sr)
#放大局部查看
n0 = 9000
n1 = 9100
plt.figure(figsize=(14,5))
plt.plot(x[n0:n1])
plt.grid()
plt.show()