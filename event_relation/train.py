import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Bidirectional, LSTM, GlobalMaxPooling1D, Dropout, Dense, \
    Concatenate
from tensorflow.keras.models import Model
import numpy as np

# Параметры модели
max_len_text = 200  # длина каждого из двух текстов
max_len_context = 1000  # длина контекстного текста
vocab_size = 20000  # размер словаря
embedding_dim = 300  # размер эмбеддинга
lstm_units = 128  # количество юнитов в LSTM
num_classes = 6  # число классов для классификации

# Определяем входы
input_text1 = Input(shape=(max_len_text,), name="text1")
input_text2 = Input(shape=(max_len_text,), name="text2")
input_context = Input(shape=(max_len_context,), name="context")

# Общий слой эмбеддингов
embedding_layer = Embedding(input_dim=vocab_size, output_dim=embedding_dim, name="embedding")

embedded_text1 = embedding_layer(input_text1)
embedded_text2 = embedding_layer(input_text2)
embedded_context = embedding_layer(input_context)

# Обработка текстов через Bidirectional LSTM с возвратом последовательностей
lstm_text1 = Bidirectional(LSTM(lstm_units, return_sequences=True))(embedded_text1)
pool_text1 = GlobalMaxPooling1D()(lstm_text1)

lstm_text2 = Bidirectional(LSTM(lstm_units, return_sequences=True))(embedded_text2)
pool_text2 = GlobalMaxPooling1D()(lstm_text2)

lstm_context = Bidirectional(LSTM(lstm_units, return_sequences=True))(embedded_context)
pool_context = GlobalMaxPooling1D()(lstm_context)

# Объединяем извлечённые признаки
concat_features = Concatenate()([pool_text1, pool_text2, pool_context])
drop = Dropout(0.5)(concat_features)
dense1 = Dense(64, activation='relu')(drop)
output = Dense(num_classes, activation='softmax')(dense1)

# Собираем модель
model = Model(inputs=[input_text1, input_text2, input_context], outputs=output)

# Компиляция модели
model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

# Вывод структуры модели
model.summary()

# Пример создания фиктивного датасета для демонстрации
n_samples = 1000
X_text1 = np.random.randint(1, vocab_size, size=(n_samples, max_len_text))
X_text2 = np.random.randint(1, vocab_size, size=(n_samples, max_len_text))
X_context = np.random.randint(1, vocab_size, size=(n_samples, max_len_context))
y = tf.keras.utils.to_categorical(np.random.randint(0, num_classes, size=(n_samples,)), num_classes=num_classes)

# Обучение модели
model.fit(
    [X_text1, X_text2, X_context], y,
    batch_size=32,
    epochs=10,
    validation_split=0.2
)
