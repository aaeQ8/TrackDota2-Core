import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
import skimage.segmentation as seg
import matplotlib.patches as patches
from skimage.measure import regionprops
from PIL import Image


class HeroesExtractor:
    def __init__(self):

        self.COORDS = self._create_rect(550, 10, 310, 25)
        self.COORDS2 = self._create_rect(1065, 10, 310, 25)

    def _create_rect(self, x1, y1, x2, y2):
        rect = patches.Rectangle((x1, y1), x2, y2)

        coords = [
            rect.get_xy(),
            [rect.get_x() + rect.get_width(), rect.get_y()],
            [rect.get_x() + rect.get_width(), rect.get_y() + rect.get_height()],
            [rect.get_x(), rect.get_y() + rect.get_height()],
        ]

        return coords

    def _crop_heroes(self, image, coords):  # pass image as numpy array

        cropped_img = image[coords[0][1] : coords[2][1], coords[0][0] : coords[2][0]]

        image_slic = seg.slic(
            cropped_img, n_segments=5, compactness=1000, start_label=1
        )

        props = regionprops(label_image=image_slic)

        hero_icons = []
        for reg in props:
            r0, c0, r1, c1 = reg.bbox
            hero_img = cropped_img[r0:r1, c0:c1]

            hero_icons.append(hero_img)

        return hero_icons  # python array of all heroes extracted from image according to COORDS

    def extract_heroes(self, image):

        heroes_icons = [
            *self._crop_heroes(image, self.COORDS),
            *self._crop_heroes(image, self.COORDS2),
        ]
        return heroes_icons

    def convert_images_for_model(self, extracted_heroes):
        h, w = 50, 20
        extracted_heroes = [
            np.array(Image.fromarray(im).convert("RGB").resize((h, w))).flatten()
            for im in extracted_heroes
        ]
        return extracted_heroes

    def save_extracted_hero(self, image, path):
        img_to_save = Image.fromarray(image).convert("RGB")
        img_to_save.save(path)


class HeroesClassifer:
    def __init__(self, X_train, y_train):

        # self.training_data = training_data

        self.X_train = X_train
        self.y_train = y_train
        self.clf = LinearDiscriminantAnalysis()
        self.clf.fit(self.X_train, self.y_train)

    def predict(self, data):
        return self.clf.predict(data)
