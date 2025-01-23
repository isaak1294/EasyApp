import anthropic
import json
import os
from pathlib import Path
from datetime import datetime
import subprocess

os.environ['ANTHROPIC_API_KEY'] = ''

def compile_tex(tex_path, output_pdf_path):
    """Compiles a LaTeX file into a PDF using pdflatex and removes auxiliary files."""
    output_dir = os.path.dirname(output_pdf_path)
    tex_file_name = os.path.basename(tex_path)
    pdf_file_name = os.path.basename(output_pdf_path)

    try:
        # Run pdflatex command
        subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory", output_dir,
                tex_file_name,
            ],
            check=True,
            cwd=os.path.dirname(tex_path),  # Set working directory to the .tex file's location
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"PDF created successfully at: {output_pdf_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error during pdflatex execution: {e.stderr.decode()}")

def remove_aux_files(tex_dir):
        # Remove auxiliary files
        base_name = os.path.splitext(tex_dir)[0]
        aux_ext = [".log", ".aux", ".out"]
        for ext in aux_ext:
             cur_file = f"{base_name}{ext}"
             if os.path.exists(cur_file):
                  os.remove(cur_file)

class ResumeGenerator:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        
    def generate_and_save(self, job_info, qualifications, resume_template, cv_template, output_format="tex"):
        """Generate and save resume/cover letter in specified format"""
        # Create output directory if it doesn't exist
        output_dir = Path(f"generated_applications/{job_info['id']}-{datetime.now().strftime('%Y%m%d')}")

        #Check if file has already been generated
        if os.path.exists(output_dir):
            exit
        else:
            output_dir.mkdir(parents=True, exist_ok=True)
            job_title = job_info['title']
            print(job_title)
            if job_title.startswith("NEW "):
                job_title = job_title[4:]
            print(job_title)
            
            # More specific resume prompt
            resume_prompt = f"""
            You are going to add content to a resume template. The template contains markers like %EXPERIENCE_HERE%, %SKILLS_HERE%, etc.
            
            Important instructions:
            1. DO NOT modify ANY existing content in the template
            2. ONLY add content where there are %MARKER% placeholders
            3. Keep the exact same LaTeX formatting style as the template
            4. Choose only the most relevant qualifications from this list: {qualifications}
            5. Don't write any additional response or comments, just the complete resume
            6. Make sure it is compilable in latex (all syntax is properly formatted, dont use '&') ALL OPENING BRACES HAVE MATCHING CLOSING BRACES!!!!

            Job Details:
            Position: {job_title}
            Company: {job_info['employer']}
            Description: {job_info['description']}
            Duration: {job_info['duration']}
            Special Requirements: {job_info['special_reqs']}
            
            Template:
            {resume_template}
            
            Replace ONLY the %MARKER% placeholders with appropriate content while preserving ALL other template content exactly as is.
            Make sure to output the full resume.
            """
            
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": resume_prompt}
                ]
            )

            resume_content = message.content[0].text
            
            
            # Create sanitized filename
            safe_title = "".join(c for c in job_info['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_employer = "".join(c for c in job_info['employer'] if c.isalnum() or c in (' ', '-', '_')).strip()

            resume_filename = output_dir / f"resume_{safe_employer}.{output_format}"
            
            # Save resume
            with open(resume_filename, "w", encoding='utf-8') as f:
                f.write(resume_content)
            
            print(f"Resume saved as: {resume_filename}")

            i = 1
            while i < 3:
                try:
                    compile_tex(
                        resume_filename,
                        f"package/{resume_filename}.pdf"
                    )
                    break
                except subprocess.CalledProcessError as e:
                    print(f"PDF generation failed {i} time(s), retrying")
                    i += 1
                    message = self.client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=4000,
                        messages=[
                            {"role": "user", "content": resume_prompt}
                        ]
                    )
                    resume_content = message.content[0].text
            
                    # Save resume
                    with open(resume_filename, "w", encoding='utf-8') as f:
                        f.write(resume_content)
                print("Error generating pdf, you're cooked.")
                return

            removal_destination = output_dir / f"package/resume_{safe_employer}.pdf"
            remove_aux_files(removal_destination)

            cover_letter_filename = output_dir /  f"cover_letter_{safe_employer}.{output_format}"

            
            # More specific cover letter prompt
            cover_letter_prompt = f"""
            You are going to add content to a cover letter template. The template contains markers like %topic relevant the job and an example of me engaging with the topic%, %Company%, %Location% etc.
            
            Important instructions:
            1. DO NOT modify ANY existing content in the template
            2. ONLY add content where there are %MARKER% placeholders
            3. Keep the exact same LaTeX formatting style as the template
            4. Choose only the most relevant qualifications from this list: {qualifications}
            5. Don't write any additional response or comments, just the cover letter
            6. Make sure it is compilable in latex (valid start and end document, dont use '&'). END THE DOCUMENT PROPERLY WITH A CURLY BRACE!!!!!!!
            
            Job Details:
            Position: {job_title}
            Company: {job_info['employer']}
            Description: {job_info['description']}
            Duration: {job_info['duration']}
            Special Requirements: {job_info['special_reqs']}
            
            Template:
            {cv_template}
            
            Replace ONLY the %MARKER% placeholders with appropriate content while preserving ALL other template content exactly as is.
            """
            
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": cover_letter_prompt}
                ]
            )

            cv_content = message.content[0].text
            
            # Save cover letter
            with open(cover_letter_filename, "w", encoding='utf-8') as f:
                f.write(cv_content)
            
            print(f"Cover letter saved as: {cover_letter_filename}")

            i = 1
            while i < 3:
                try:
                    compile_tex(
                        cover_letter_filename,
                        f"package/{cover_letter_filename}.pdf"
                    )
                    break
                except subprocess.CalledProcessError as e:
                    print(f"Latex generation failed {i} time(s), retrying")
                    i += 1
                    message = self.client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=4000,
                        messages=[
                            {"role": "user", "content": cover_letter_prompt}
                        ]
                    )
                    cv_content = message.content[0].text
            
                    # Save cover letter
                    with open(cover_letter_filename, "w", encoding='utf-8') as f:
                        f.write(cv_content)
                print("Error generating latex, you're cooked.")
                return

            # Remove log files
            removal_destination = output_dir / f"package/cover_letter_{safe_employer}.pdf"
            remove_aux_files(removal_destination)


def main():
    user_input = input("input the ids of the jobs you want to apply for separated by spaces")
    ids = list(map(str, user_input.split()))
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
        
    # Initialize generator
    generator = ResumeGenerator(api_key)

    # Load qualifications
    with open ('qualifications.md', "r") as f:
        qualifications = f.read()
    
    # Load templates
    try:
        with open("templates/resumeTemplate.tex", "r") as f:
            resume_template = f.read()
    except FileNotFoundError:
        print("No template exists, generating one")
        subprocess.run(["python", "alsoinitial.py"])
        with open("templates/resumeTemplate.tex", "r") as f:
            resume_template = f.read()

    try:
        with open("templates/CVTemplate.tex", "r") as f:
            cv_template = f.read()
    except FileNotFoundError:
        print("No template exists, generating one")
        subprocess.run(["python", "alsoinitial.py"])
        with open("templates/CVTemplate.tex", "r") as f:
            cv_template = f.read()
        
    # Load jobs data
    with open("puppeteer/jobs.json", "r") as f:
        jobs_data = json.load(f)
        
    
    # Process each job
    print(ids)
    for job in jobs_data:
        # Load detailed job description
        job_id = job.get('id', '')
        print(job_id)
        if job_id not in ids:
            continue
            
        try:
            with open(f"puppeteer/jobs/job-{job_id}.json", "r") as f:
                job_desc = json.load(f)
                # Process the job description as needed
                print(f"Loaded job description for ID {job_id}")
        except FileNotFoundError:
            # Log or handle the missing file scenario
            print(f"File for job ID {job_id} not found. Skipping to the next job.")
            continue
                
            # Combine job info
        job_info = {
            'id' : job.get('id', ''),
            'title': job.get('title', ''),
            'employer': job.get('employer', ''),
            'division': job.get('division', ''),
            'description': job_desc.get('Job Description:', ''),
            'qualifications': job_desc.get('Qualifications:', ''),
            'special_reqs': job_desc.get('Special Job Requirements:', ''),
            'duration': job_desc.get('Co-op Work term Duration:', '')
        }

            # Generate and save resume (removed client parameter)
        generator.generate_and_save(job_info, qualifications, resume_template, cv_template, output_format="tex")
            
if __name__ == "__main__":
    main()