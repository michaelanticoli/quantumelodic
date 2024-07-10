import streamlit as st
import openai
import pandas as pd
import time

class KnowledgeBase:
    def __init__(self):
        self.data = {}

    def add_term(self, term, astrology, music, math):
        self.data[term.lower()] = {
            "Astrology": astrology,
            "Music": music,
            "Mathematics": math
        }

    def get_term_info(self, term):
        term = term.lower()
        if term in self.data:
            return self.data[term]
        else:
            return None

    def get_all_terms(self):
        return self.data

# Create the knowledge base
kb = KnowledgeBase()

# OpenAI API setup
openai.api_key = "YOUR_OPENAI_API_KEY"

def generate_descriptions(term):
    prompt = f"""
    Provide a detailed description for the term '{term}' in the context of astrology, music, and mathematics. 
    For astrology, include the definition, key points, and an example. 
    For music, include an analogy, key points, and an example.
    For mathematics, include the concept, key points, and an example.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response['choices'][0]['message']['content'].strip()

        # Parse the response to extract astrology, music, and mathematics sections
        try:
            if "For astrology:" in content and "For music:" in content and "For mathematics:" in content:
                astrology_section = content.split("For astrology:")[1].split("For music:")[0].strip()
                music_section = content.split("For music:")[1].split("For mathematics:")[0].strip()
                math_section = content.split("For mathematics:")[1].strip()

                astrology_description = {
                    "Definition": astrology_section.split("Key Points:")[0].strip(),
                    "Key Points": [point.strip() for point in astrology_section.split("Key Points:")[1].split("Example:")[0].split(',')],
                    "Example": astrology_section.split("Example:")[1].strip()
                }

                music_description = {
                    "Analogy": music_section.split("Key Points:")[0].strip(),
                    "Key Points": [point.strip() for point in music_section.split("Key Points:")[1].split("Example:")[0].split(',')],
                    "Example": music_section.split("Example:")[1].strip()
                }

                math_description = {
                    "Concept": math_section.split("Key Points:")[0].strip(),
                    "Key Points": [point.strip() for point in math_section.split("Key Points:")[1].split("Example:")[0].split(',')],
                    "Example": math_section.split("Example:")[1].strip()
                }

                return astrology_description, music_description, math_description

            else:
                st.error(f"Missing expected headers in response for term '{term}'. Full response:\n{content}")
                return None, None, None

        except Exception as e:
            st.error(f"Error parsing the response for term '{term}': {e}")
            st.text(content)  # Display the full response for debugging
            return None, None, None

    except Exception as e:
        st.error(f"Error generating descriptions for term '{term}': {e}")
        return None, None, None

# Streamlit UI
st.title("Astrology, Music, and Mathematics Knowledge Base")

# Adding new terms in batches
with st.form(key='add_term_form'):
    st.header("Add New Terms")
    terms = st.text_area("Enter terms separated by commas")
    batch_size = st.number_input("Batch size", min_value=1, max_value=50, value=20)
    submit_button = st.form_submit_button(label='Add Terms')

    if submit_button:
        terms_list = [term.strip() for term in terms.split(',')]
        total_terms = len(terms_list)
        batches = [terms_list[i:i + batch_size] for i in range(0, total_terms, batch_size)]
        
        for i, batch in enumerate(batches):
            st.info(f"Processing batch {i + 1} of {len(batches)}...")
            for term in batch:
                if term:
                    astrology, music, math = generate_descriptions(term)
                    if astrology and music and math:
                        kb.add_term(term, astrology, music, math)
                    time.sleep(1)  # Add delay to avoid hitting rate limits
            st.success(f"Batch {i + 1} processed successfully!")
        st.success("All terms added successfully!")

# Retrieve and display all terms
st.header("All Terms")
all_terms = kb.get_all_terms()
if all_terms:
    df = pd.DataFrame([
        {
            "Term": term,
            "Astrology Definition": details["Astrology"]["Definition"],
            "Astrology Key Points": ", ".join(details["Astrology"]["Key Points"]),
            "Astrology Example": details["Astrology"]["Example"],
            "Music Analogy": details["Music"]["Analogy"],
            "Music Key Points": ", ".join(details["Music"]["Key Points"]),
            "Music Example": details["Music"]["Example"],
            "Mathematics Concept": details["Mathematics"]["Concept"],
            "Mathematics Key Points": ", ".join(details["Mathematics"]["Key Points"]),
            "Mathematics Example": details["Mathematics"]["Example"]
        }
        for term, details in all_terms.items()
    ])
    st.dataframe(df)

    # Provide a download link for the CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='knowledge_base.csv',
        mime='text/csv',
    )
