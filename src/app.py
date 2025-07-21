import sys
import os

# Add the project root to the system path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- START POPPLER PATH CONFIGURATION FOR DEPLOYMENT ---
# This block specifically helps pdf2image find Poppler in Streamlit Cloud
# It assumes Poppler might be available in a common location or attempts to set it
try:
    if os.environ.get("STREAMLIT_SERVER_PORT"): # Check if running on Streamlit Cloud
        # Common paths for Poppler on Linux-based cloud environments
        # You might need to adjust this based on actual Poppler installation path
        # A common one is /usr/bin/ which should be in PATH anyway, but explicit set can help
        # If Streamlit Cloud installs poppler-utils, it should be discoverable
        # However, sometimes pdf2image needs the path to the bin directory.
        # Let's try pointing directly to the poppler_path
        # For environments that install poppler-utils, this is often implicitly handled,
        # but sometimes an explicit path for pdf2image helps.
        # Let's try to set it only if it's not already set.
        if "POPPLER_PATH" not in os.environ:
             # This path is a common default for poppler-utils installation on Ubuntu/Debian like systems
             # This line is more about making pdf2image explicitly aware of where to look.
             # No need to set if packages.txt properly works.
            pass # We rely on packages.txt for this. Let's not override system PATH
    else:
        # For local Windows development, you need Poppler in your local PATH
        # This 'else' block is for local troubleshooting/reminders, not for deployment logic
        pass
except Exception as e:
    # Log this but don't stop the app from starting
    print(f"DEBUG: Poppler path setup failed: {e}")
# --- END POPPLER PATH CONFIGURATION ---

from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
import json

# Import the utility function from the new structure
from src.utils.pdf_processor import input_pdf_setup
from pdf2image.exceptions import PopplerNotInstalledError # Add this import for specific error handling

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
# Instruction for file upload
st.write("Upload a job description and your resume (PDF) to get a percentage match!")
st.subheader("1. Enter Job Description")
input_text = st.text_area("Job Description", key="input", height=200)

# RE-ADDED: File Uploader Section
st.subheader("2. Upload Your Resume")
uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

if uploaded_file is not None:
    st.success("PDF Uploaded Successfully!")

submit = st.button("Calculate Percentage Match")


if submit:
    if uploaded_file is not None:
        with st.spinner("Processing your resume and job description..."):
            try:
                pdf_content = input_pdf_setup(uploaded_file)
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

            except PopplerNotInstalledError: # Catch specific Poppler error
                st.error("Error: Poppler is not installed or not found. Please contact support if this is on a deployed app.")
            except FileNotFoundError as e:
                st.error(f"File Error: {e}. Please ensure a valid PDF is uploaded.")
            except json.JSONDecodeError:
                st.error("Error: Could not parse the model's response. The AI might have returned an unexpected format. Please try again.")
                st.write("Raw response:", response_json_str)
            except Exception as e:
                st.error(f"An unexpected error occurred during processing: {e}")
                st.write("Please check the console for more details.")

    else:
        st.warning("Please upload a resume to get a match!")