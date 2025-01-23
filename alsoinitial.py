import anthropic
import json
import os
from pathlib import Path
from datetime import datetime
import subprocess
import pdfplumber


class TemplateGenerator:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_and_save(self, res, cov, res_template, cov_template):
        output_dir = Path("templates")

        res_prompt = f"""
        This is for a program that generates resumes and cover letters from templates. For ease of use and efficiency, the templates are 
        populated with basic user information. The users upload their own resumes and I need you to simply migrate their information to
        the template. Within the template, I have surrounded certain portions with '&' ex) &NAME& and I need you to replace all
        of those with the relevant information from the resume.
        
        Important instructions:
        1. Ignore any section where there are %MARER% placeholders. Do not do the instructions inside and do not edit them.
        2. ONLY add content where there are &MARKER& placeholders
        3. Keep the exact same LaTeX formatting style as the template
        4. Don't write any additional response or comments, just the complete template
        5. Make sure it is compilable in latex (all syntax is properly formatted, dont use '&') ALL OPENING BRACES HAVE MATCHING CLOSING BRACES!!!!
        
        Template to populate: {res_template}
        Resume: {res}

        Replace ONLY the &MARKER& placeholders with appropriate content while preserving template formatting and preserving the %MARKER% placeholders.
        Make sure to output the full resume.
        """

        message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": res_prompt}
                ]
            )
        
        res_temp_content = message.content[0].text

        res_temp_filename = "templates/resumeTemplate.tex"

        with open(res_temp_filename, "w", encoding='utf-8') as f:
            f.write(res_temp_content)

        cov_prompt = f"""
        Fill in the information in the provieded template with information from the provided cover letter. Remove any information pertaining 
        to a specific job, and add the following. Do not change or remove any of the %MARKER% placeholders:

        1. Replace the &MARKER& placeholders with relevant information
        2. Don't write any additional response or comments, just the complete template
        3. Make sure it is compilable in latex (all syntax is properly formatted, dont use '&') ALL OPENING BRACES HAVE MATCHING CLOSING BRACES!!!!
        
        Replace ONLY the &MARKER& placeholders with appropriate content while preserving template formatting and preserving the %MARKER% placeholders.
        Make sure to output the full cover letter.

        Template to populate: {cov_template}
        Resume: {cov}
        """

        message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": cov_prompt}
                ]
            )
        
        cov_temp_content = message.content[0].text

        cov_temp_filename = "templates/CVTemplate.tex"

        with open(cov_temp_filename, "w", encoding='utf-8') as f:
            f.write(cov_temp_content)

def main():
    # Load API key from json
    with open('local.json', 'r') as f:
        user_data = json.load(f)
        os.environ['ANTHROPIC_API_KEY'] = user_data.get('api_key', '')
        api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        os.environ['ANTHROPIC_API_KEY'] = input("Please input a valid Anthropic API key:")
        api_key = os.getenv('ANTHROPIC_API_KEY')
        user_data["api_key"] = api_key
        with open('local.json', 'w') as f:
            json.dump(user_data, f, indent=4)

    generator = TemplateGenerator(api_key)
    res = ""
    cov = ""

    with open("templates/resumeTemplateTemplate.tex", "r") as f:
        res_template = f.read()

    try:
        with pdfplumber.open("current_documents/resume.pdf") as f:
            for page in f.pages:
                res = res + page.extract_text()
                print(res)
    except FileNotFoundError:
        print("Please add your current resume content to the current_documents folder and title it \"resume.pdf\"")
        return

    with open("templates/CVTemplateTemplate.tex", "r") as f:
        cov_template = f.read()

    try:
        with pdfplumber.open("current_documents/cover.pdf") as f:
            for page in f.pages:
                cov = cov + page.extract_text()
    except FileNotFoundError:
        print("Please add your current cover letter to the current_documents folder and title it \"cover.pdf\"")
        return

    generator.generate_and_save(res, cov, res_template, cov_template)


if __name__ == "__main__":
    main()
    
    

