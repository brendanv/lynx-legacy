from bs4 import BeautifulSoup

class Heading:
    def __init__(self, display, id):
        self.id = id
        self.display = display

    def to_list(self): 
        return [self.display, self.id]

    def to_dict(self):
        return {'id': self.id, 'display': self.display}

class HTMLCleaner:
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, features="lxml")
        self.headings = []

    def generate_headings(self):
        viable_levels = ['h1', 'h2', 'h3']
        doc_headings = []
        for level in viable_levels:
            level_headings = self.soup.find_all(level)
            if len(level_headings) > 0:
                doc_headings = level_headings
                break

        self.headings = []
        id_counter = 1
        for tag in doc_headings:
            tag['id'] = f"heading_{id_counter}"
            label = tag.get_text()
            self.headings.append(Heading(label, tag['id']))
            id_counter += 1

        return self

    def get_headings(self):
        return self.headings

    def replace_image_links_with_images(self):
        image_links = self.soup.find_all('a', class_='image-link')
        for link in image_links:
            new_img_tag = self.soup.new_tag('img', src=link['href'])
            link.replace_with(new_img_tag)

        return self

    def prettify(self) -> str:
        return self.soup.prettify(formatter='html')