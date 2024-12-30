Image Converter App 🧉
A user-friendly image converter application built with Python and Tkinter. This application allows you to convert images to various formats (JPG, PNG, WEBP), resize them, and optimize their quality, all within a graphical interface.

Features
Image Format Conversion: Convert images to JPG, PNG, or WEBP.
Batch Processing: Select and convert multiple images at once.
Image Preview: Preview images before conversion.
Resize Images: Option to resize images while maintaining aspect ratio.
Preserve Metadata: Retain EXIF metadata during conversion.
Progress Tracking: Real-time progress bar for ongoing conversions.
Error Handling: Informative messages for unsupported or invalid files.
Cancel Conversion: Stop ongoing conversion processes.
Requirements
Python 3.8 or higher
Required libraries:
tkinter
Pillow
threading
Installation
Clone this repository:

bash
Copiar código
git clone https://github.com/yourusername/image-converter.git
cd image-converter
Install the required dependencies:

bash
Copiar código
pip install -r requirements.txt
Run the application:

bash
Copiar código
python main.py
Usage
Select Images: Use the "Select Images" button to choose files for conversion.
Choose Options: Select desired output format, resize settings, and optimization.
Convert: Click on the format button (Convert to PNG, Convert to JPG, Convert to WEBP) to start the conversion.
Cancel Conversion: If needed, cancel the process by clicking the Cancel Conversion button.
View Results: Check the output directory for converted files.
Project Structure
bash
Copiar código


Future Enhancements
Add support for additional image formats.
Include drag-and-drop functionality.
Introduce CLI options for advanced users.
Add localization for multi-language support.
License
This project is licensed under the MIT License.

Contribution
Contributions are welcome! Please open an issue or submit a pull request to contribute.

Acknowledgements
Pillow for image processing.
The Python and Tkinter communities for their valuable resources.


Charlesagui 