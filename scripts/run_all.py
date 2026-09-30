"""Run the complete available analysis without the original research archive."""
from pathlib import Path
import argparse
import shutil
import subprocess
import sys

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rscript',default=shutil.which('Rscript'),help='Path to Rscript (base R is sufficient).')
    args=parser.parse_args()
    if not args.rscript:
        parser.error('Rscript was not found. Install R or pass --rscript with its location.')
    scripts=Path(__file__).resolve().parent
    commands=[[sys.executable,str(scripts/'reproduce.py')],
              [args.rscript,'--vanilla',str(scripts/'discussion.R')],
              [args.rscript,'--vanilla',str(scripts/'plot_downsampling.R')],
              [sys.executable,str(scripts/'embed_pdf_fonts.py')]]
    for command in commands:
        subprocess.run(command,check=True)
    print('Available analyses completed. IDM/Gipps evidence remains pending recovery.')

if __name__=='__main__':main()
