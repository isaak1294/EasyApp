import subprocess
import os

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
        raise

def remove_aux_files(tex_dir):
        # Remove auxiliary files
        base_name = os.path.splitext(tex_dir)[0]
        aux_ext = [".log", ".aux", ".out"]
        for ext in aux_ext:
             cur_file = f"{base_name}{ext}"
             if os.path.exists(cur_file):
                  os.remove(cur_file)
                


# Usage
compile_tex(
    "generated_applications/244688-20241230/resume_Nasdaq.tex",
    "package/resume_Nasdaq.pdf"
)

remove_aux_files("generated_applications/244688-20241230/resume_Nasdaq.tex")