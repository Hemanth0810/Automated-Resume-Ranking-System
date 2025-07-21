import sys # ADD THIS LINE
import os  # ADD THIS LINE (if not already present, it usually is)

# ADD THESE LINES TO FIX THE ModuleNotFoundError ON DEPLOYMENT
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
import json

# Import the utility function from the new structure
from src.utils.pdf_processor import input_pdf_setup

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def Automated_Resume_Ranking_System(job_description , pdf_content):
  prompt_1 = f"""
  Extract the designation of the job from job description
  Extract the key words from job description
  Final output is the designation and keywords in json format
  job description:
  {job_description}
  """
  prompt_2 = f"""
  Extract the designation from this resume
  Extract the key words from this resume
  Final output is the designation and keywords in json format
  """
  model1 =  genai.GenerativeModel('gemini-pro')
  try:
      response_job = model1.generate_content(prompt_1)
      response_job = response_job.text.replace("\n","")
  except Exception as e:
      st.error(f"Error extracting job description keywords: {e}")
      return json.dumps({"error": f"Failed to process job description: {e}"})

  model2 =  genai.GenerativeModel('gemini-pro-vision')
  try:
      response_resume = model2.generate_content([prompt_2,pdf_content])
      response_resume = response_resume.text.replace("\n","")
  except Exception as e:
      st.error(f"Error extracting resume keywords: {e}")
      return json.dumps({"error": f"Failed to process resume: {e}"})


  prompt_3 = f"""
  job:
  {response_job}
  resume:
  {response_resume}
  show output in json format:
  Designation Match : Give me the semantic percentage match of destination of job and resume in number.
  Semantic Keyword Match : Give the semantic percentage match of keywords in job and resume in number.
  Final Match : Give me the final sematic match between job and resume in number.
  """

  try:
      response_final = model1.generate_content(prompt_3)
      response_final = response_final.text.replace("\n","")
  except Exception as e:
      st.error(f"Error comparing job and resume: {e}")
      return json.dumps({"error": f"Failed to compare job and resume: {e}"})

  return response_final


# Streamlit App
st.set_page_config(page_title="Automated Resume Ranking System")
st.header("Automated Resume Ranking System")
# Updated instruction for hardcoded PDF
st.write("This system processes the predefined 'sample_resume.pdf' against your job description.")
st.subheader("1. Enter Job Description")
input_text = st.text_area("Job Description", key="input", height=200)

# REMOVED: st.subheader("2. Upload Your Resume")
# REMOVED: uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])
# REMOVED: if uploaded_file is not None:
# REMOVED:     st.success("PDF Uploaded Successfully!")

submit = st.button("Calculate Percentage Match")


if submit:
    # --- START OF HARDCODED PDF READING ---
    try:
        # Read the predefined PDF directly
        with open('sample_resume.pdf', 'rb') as f:
            raw_pdf_bytes = f.read()

        # Pass the raw bytes to your input_pdf_setup function
        # Mimic UploadedFile object for input_pdf_setup by providing a dictionary with a 'read' method
        pdf_content = input_pdf_setup({"read": lambda: raw_pdf_bytes})

        with st.spinner("Processing predefined resume and job description..."):
            response_json_str = Automated_Resume_Ranking_System(input_text, pdf_content[0])

        if "error" in response_json_str:
            response_data = json.loads(response_json_str)
            st.error(f"Processing failed: {response_data.get('error', 'Unknown error during API call.')}")
        else:
            response_data = json.loads(response_json_str)

            st.subheader("Matching Results:")

            if "Designation Match" in response_data:
                designation_match = response_data["Designation Match"]
                st.metric(label="Designation Match", value=f"{designation_match}%")
            if "Semantic Keyword Match" in response_data:
                keyword_match = response_data["Semantic Keyword Match"]
                st.metric(label="Semantic Keyword Match", value=f"{keyword_match}%")
            if "Final Match" in response_data:
                final_match = response_data["Final Match"]
                st.metric(label="Overall Match", value=f"{final_match}%", delta=f"{final_match - 50:.1f}% from average")

            st.markdown("---")
            st.write("Raw Model Output (for debugging):")
            st.json(response_data)

    except FileNotFoundError:
        st.error("Error: 'sample_resume.pdf' not found. Please ensure it is in the 'src' directory.")
    except json.JSONDecodeError:
        st.error("Error: Could not parse the model's response. The AI might have returned an unexpected format. Please try again.")
        st.write("Raw response:", response_json_str)
    except Exception as e:
        st.error(f"An unexpected error occurred during processing: {e}")
        st.write("Please check the console for more details.")

    # --- END OF HARDCODED PDF READING ---

# REMOVED: else:
# REMOVED: st.warning("Please upload a resume to get a match!")