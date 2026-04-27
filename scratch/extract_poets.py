import os
import re

directory = r'C:\Users\ariro\OneDrive\Documents\Psalms\data\literary_echoes'
output_file = 'literary_echoes_summary.md'

results = []

for filename in os.listdir(directory):
    if filename.endswith('.txt') and filename.startswith('psalm_'):
        psalm_num = filename.split('_')[1]
        psalm_name = f"Psalm {int(psalm_num)}"
        
        path = os.path.join(directory, filename)
        poets = set()
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('#### '):
                    # Check if it's a Psalm header
                    if 'Psalm' in line and ':' in line:
                        continue
                        
                    content = line[5:].strip() # Remove #### 
                    
                    # Special case for split names like W.B. \n Yeats
                    if re.match(r'^[A-Z]\.[A-Z]\.?$', content) or content.endswith('.'):
                        # Look ahead for the next line
                        next_idx = i + 1
                        while next_idx < len(lines) and not lines[next_idx].strip():
                            next_idx += 1
                        if next_idx < len(lines):
                            next_line = lines[next_idx].strip()
                            # If it looks like a continuation (starts with a word and has a comma or italics)
                            if next_line and not next_line.startswith('#'):
                                content = content + " " + next_line
                    
                    # Now parse the content
                    # Format: Poet Name, *Work* (Year)
                    # We want the poet name.
                    # Handle "Vyasa (attributed)" -> Vyasa
                    # Handle "The Qur'an" -> The Qur'an
                    # Handle "*Enuma Elish*" -> Enuma Elish
                    
                    # Split by comma first
                    parts = content.split(',')
                    name = parts[0].strip()
                    
                    # Remove italics markdown
                    name = name.replace('*', '')
                    
                    # Remove (attributed)
                    name = re.sub(r'\(attributed\)', '', name, flags=re.IGNORECASE).strip()
                    
                    # If it's a work name that starts with * but no poet was provided
                    # e.g. #### *Enuma Elish*
                    # In this case 'name' is already cleaned up.
                    
                    if name:
                        poets.add(name)
        
        results.append({
            'psalm': psalm_name,
            'poets': sorted(list(poets))
        })

# Sort results by psalm number
results.sort(key=lambda x: int(x['psalm'].split(' ')[1]))

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Literary Echoes Summary\n\n")
    f.write("| Psalm | Poets / Sources |\n")
    f.write("|-------|-----------------|\n")
    for r in results:
        # Join and clean up common patterns
        poets_str = ', '.join(r['poets'])
        f.write(f"| {r['psalm']} | {poets_str} |\n")

print(f"Summary written to {output_file}")
