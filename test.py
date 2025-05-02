import csv

input_file = 'results.csv'
output_file = 'results3.csv'

with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
     open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    for row in reader:
        row.extend(['0'])
        writer.writerow(row)
