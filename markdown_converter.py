import markdown
from bs4 import BeautifulSoup
from PIL import Image
import os
import re
import base64
from io import BytesIO

class MarkdownConverter:
    def __init__(self, image_size=(800, 600), image_dir="images"):
        self.image_size = image_size
        self.image_dir = image_dir
        os.makedirs(self.image_dir, exist_ok=True)

    def _process_images(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')
            caption = title if title else alt
            
            if src.startswith(('http://', 'https://')):
                try:
                    import requests
                    response = requests.get(src)
                    img_data = response.content
                except Exception as e:
                    print(f"Error downloading image {src}: {e}")
                    continue
            else:
                try:
                    with open(src, 'rb') as f:
                        img_data = f.read()
                except Exception as e:
                    print(f"Error reading local image {src}: {e}")
                    continue

            try:
                image = Image.open(BytesIO(img_data))
                image = image.resize(self.image_size, Image.Resampling.LANCZOS)
                
                filename = f"processed_{hash(src)}.png"
                output_path = os.path.join(self.image_dir, filename)
                image.save(output_path)
                
                figure = soup.new_tag('figure')
                figure['class'] = 'image-caption'
                
                new_img = soup.new_tag('img')
                new_img['src'] = os.path.relpath(output_path, os.path.dirname(self.image_dir))
                new_img['alt'] = alt
                figure.append(new_img)
                
                if caption:
                    figcaption = soup.new_tag('figcaption')
                    figcaption.string = caption
                    figure.append(figcaption)
                
                img.replace_with(figure)
                
            except Exception as e:
                print(f"Error processing image {src}: {e}")

        return str(soup)

    def convert(self, markdown_text):
        mathjax_config = """
        <script type="text/x-mathjax-config">
            MathJax.Hub.Config({
                tex2jax: {
                    inlineMath: [['$', '$'], ['\\(', '\\)']],
                    displayMath: [['$$', '$$'], ['\\[', '\\]']],
                    processEscapes: true
                },
                "HTML-CSS": {
                    linebreaks: { automatic: true },
                    availableFonts: ["STIX"],
                    preferredFont: "STIX",
                    webFont: "STIX-Web",
                    imageFont: null,
                    undefinedFamily: "STIXGeneral,'Arial Unicode MS',serif"
                }
            });
        </script>
        <script type="text/javascript" async
            src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
        </script>
        """
        
        html = markdown.markdown(
            markdown_text,
            extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.tables',
                'markdown.extensions.fenced_code',
                'markdown.extensions.smarty',
                'markdown.extensions.toc',
                'pymdownx.tasklist'
            ]
        )
        
        html = self._process_images(html)
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                img {{ max-width: 100%; height: auto; }}
                pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; }}
                blockquote {{ border-left: 4px solid #ddd; padding-left: 15px; color: #666; }}
                code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
                .MathJax {{ font-size: 1.1em; }}
                input[type="checkbox"] {{ margin-right: 8px; }}
                .task-list-item {{ list-style-type: none; }}
                .task-list-item-checkbox {{ margin-right: 8px; }}
                figure.image-caption {{ margin: 1em 0; text-align: center; }}
                figure.image-caption img {{ display: block; margin: 0 auto; }}
                figure.image-caption figcaption {{ 
                    color: #666;
                    font-size: 0.9em;
                    margin-top: 0.5em;
                    text-align: center;
                }}
            </style>
            {mathjax_config}
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        return full_html

    def convert_file(self, input_file, output_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        html = self.convert(markdown_text)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
