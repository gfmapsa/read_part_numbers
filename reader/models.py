from django.db import models
import pandas as pd
import pdfplumber
import numpy as np
import pdfplumber
import pdfplumber.page
import pandas as pd
import pytesseract
import cv2
import re


# Create your models here.
class PdfReader(models.Model):
    def keep_visible_lines(self, obj):
        """
        If the object is a `rect type, keep it only if the lines are visible.

        A visible line is the one having `non_stroking_color as 0.
        """
        if obj['object_type'] == 'rect':
            return obj['non_stroking_color'] == (0, 0, 0)
        return True


    def find_term(self, page, term):
        results = page.search(term)
        
        if (results):
            return results[0]
        return None


    def concat_cols(self, df, col, list):
        # Nuevo DataFrame solo con las columnas Part Number
        new_df = pd.DataFrame(df)

        # Concateno las dos columnas en una sola
        duplicated_columns = new_df.loc[:, new_df.columns.duplicated(keep=False)]
        combined = pd.concat([duplicated_columns.iloc[:, i] for i in range(duplicated_columns.shape[1])], ignore_index=True)

        print(f"Se agrega {combined}\n")
        # La agrego a la lista de Part Numbers
        list.append(combined)
    
    
    def get_text_data(self, page, finder):
        coords = (finder["x0"] - 50, finder["top"] - 50, page.bbox[2], page.bbox[3])
        cropped_page = page.crop(coords)

        # Filter out hidden lines.
        cropped_page = cropped_page.filter(self.keep_visible_lines)
        ts = {
            "vertical_strategy": "lines_strict",
            "horizontal_strategy": "lines_strict",
        }
        
        """
        # Codigo para debuguear
        im = cropped_page.to_image()
        im.reset().debug_tablefinder(ts)

        im.draw_rects(page.chars)
        im.show()
        """
        
        # Busco las tablas en la pagina recortada
        tables = cropped_page.extract_tables(ts)

        part_numbers_list = []
        count_list = []
        
        sum_list_tables = []
        
        part_numbers_check = False
        count_check = False

        for table in tables:
            # Convierto a pandas para hacer manipulación de datos
            df = pd.DataFrame(table)

            part_numbers_check = False
            count_check = False

            # Puede haber mas tablas en la pagina recortada
            # Me quedo solo con las que tengan el encabezado SUM List
            if df.iloc[0].str.contains(finder["text"]).any():

                # Elimino el encabezado SUM List y pongo como primera fila las columnas
                df = df.drop(index=0).dropna(axis=1, how='all')
                df.columns = df.iloc[0]
                df = df.drop(index=1).reset_index(drop=True)

                sum_list_tables.append(df)
                
                for col in df.columns:
                    column = df[col]
                    
                    if "Part Number" in col:
                        if (column.ndim > 1):
                            
                            if (not part_numbers_check):
                                part_numbers_check = True
                                self.concat_cols(column, col, part_numbers_list)
                        else:
                            part_numbers_list.append(column)
                    
                    
                    if "Total count/length" in col:
                        if (column.ndim > 1):
                            if (not count_check):
                                count_check = True
                                self.concat_cols(column, col, count_list)
                        else:
                            count_list.append(column)


        result_part_numbers = pd.concat(part_numbers_list, ignore_index=True)
        result_count = pd.concat(count_list, ignore_index=True)

        return result_part_numbers, result_count


    def get_ocr_data(self, page):
        im = page.to_image()
        np_image = np.array(im.original)
        
        image = cv2.cvtColor(np_image, cv2.COLOR_BGR2GRAY)
        
        image = cv2.bilateralFilter(image, 9, 75, 75)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        image = clahe.apply(image)

        adaptive_thresh = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        contours, _ = cv2.findContours(adaptive_thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)

        header_pattern = re.compile(
            r'NOME.*DESCRIZIONE.*CODICE.*IVECO.*DOC.*TAB.*QUANT',
            re.IGNORECASE
        )   
        
        part_numbers = []
        last_numbers = []
        
        for contour in reversed(contours):
            x, y, w, h = cv2.boundingRect(contour)
            
            if w > 500 and h > 300:
                cv2.rectangle(np_image, (x, y), (x + w, y + h), (0,255,0), 2)
                
                table_image = np_image[y:y+h, x:x+w]
                table_text = pytesseract.image_to_string(table_image)
                
                match = header_pattern.search(table_text)
                
                if match:
                    start, end = match.span()
                    
                    if start < 100 and end < 200 :
                        
                        table_text = table_text[match.start():]

                        table_text = re.sub(r'[\[\]\|<>(){}]+', "", table_text)
                        table_text = re.sub("€", "E", table_text)
                        table_text = re.sub("£", "E", table_text)
                        table_text = re.sub(r'E(\d)', r'EZ', table_text)
                        table_text = re.sub(r'(\s)—', r'\1', table_text)
                        
                        table_text = re.sub(header_pattern, " ", table_text)
                        
                        print(table_text)
                        
                        rows = table_text.split('\n')
                        code_pattern = re.compile(r'(?<=\s)((?:\d+/)+\d+|\d{6,})(?:\s*|\W*)(E[A-Z]{1})?', re.IGNORECASE)

                        number_pattern = re.compile(r'\d+(?:\.\d+)?')

                        index = 0
                        for row in rows:
                            match = code_pattern.findall(row)
                            if match:
                                num, suffix = match[0]
                                
                                if '/' in num or int(num) > 100000:
                                    numbers_in_row = number_pattern.findall(row)
                                    
                                    if numbers_in_row:
                                        part_numbers.append(num)
                                        
                                        last_number_in_row = numbers_in_row[-1]
                                        
                                        if (last_number_in_row == "i".lower()):
                                            last_number_in_row = 1
                                            
                                        
                                        if (last_number_in_row == num):
                                            last_number_in_row = 0
                                        
                                        last_numbers.append(last_number_in_row)
                                        
                            else:
                                numbers_in_row = number_pattern.findall(row)
                                
                                if len(numbers_in_row) == 1 and len(numbers_in_row[0]) >= 6:
                                    
                                    part_numbers.append(numbers_in_row[0])
                                    last_numbers.append(0)
                            
                            index += 1   
                                    
        return part_numbers, last_numbers

    
    def read_pdf(self, pdf_file):
        pdf = pdfplumber.open(pdf_file)
        
        pages = pdf.pages
        page = pages[0]
        finder = self.find_term(page, "SUM List")

        part_numbers = []
        last_numbers = []

        if (finder == None):
            page = pages[-1]
            part_numbers, last_numbers = self.get_ocr_data(page)
        else:
            part_numbers, last_numbers = self.get_text_data(page, finder)

        return { "part_numbers": list(part_numbers), "last_numbers": list(last_numbers) }