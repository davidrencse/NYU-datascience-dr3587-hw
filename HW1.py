# David Ren - Data Science Bootcamp HW1
# Task 1
def count_vowels(word):
  vowels = "aeiou"
  vowel_num = 0
  
  for letter in word:
    if letter.lower() in vowels:
      vowel_num += 1
      
  return vowel_num 

# Task 2
animals=['tiger', 'elephant', 'monkey', 'zebra', 'panther']

for elem in animals:
  print(elem.upper())

# Task 3
for i in range(1, 21):
  if i%2 != 0:
    print(i, " is odd")
  else:
    print(i, " is even")

# Task 4
def sum_of_integers(a, b):
  return (a + b)

