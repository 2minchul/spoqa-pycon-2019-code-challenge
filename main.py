import itertools
import random
import sys

import pygame

SCREEN_WIDTH = 906
SCREEN_HEIGHT = 450

white = (255, 255, 255)
black = (0, 0, 0)

pygame.init()
pygame.display.set_caption("CONNECT THE PYTHONISTAS")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()


def crop_image(image: pygame.Surface, x, y, size):
    cropped = pygame.Surface(size)
    cropped.blit(image, (0, 0), (x, y, size[0], size[1]))
    return cropped


class ImageObject:
    x = y = 0
    image: pygame.Surface

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    def get_position(self):
        return self.x, self.y


class PuzzleImage(ImageObject):
    def __init__(self, path):
        self.image: pygame.Surface = pygame.image.load(path).convert_alpha()


class PuzzlePiece(ImageObject):
    def __init__(self, image, x, y):
        self.x = self.origin_x = x
        self.y = self.origin_y = y
        self.image = image
        self.width, self.height = self.image.get_size()

    def draw_rect(self, border=1):
        pygame.draw.rect(screen, black, [self.x, self.y, *self.image.get_size()], border)

    def is_hit(self, position):
        if self.x <= position[0] < self.x + self.width and self.y <= position[1] < self.y + self.height:
            return True
        return False


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


class PieceArray:
    array: list
    size: int

    def __init__(self, pieces, pieces_size, background_size, line_limit=3):
        self.pieces_size = pieces_size
        self.background_size = background_size
        self.size = line_limit
        self.array = [i for i in chunks(pieces, self.size)]  # 3x3 리스트로 reshape

    def loop(self):
        for i, _line in enumerate(self.array):
            for j, piece in enumerate(_line):
                if piece:
                    yield (i, j), piece

    def flatten_array(self):
        return itertools.chain(*self.array)

    def find_hit(self, position):
        for index, piece in self.loop():
            if piece.is_hit(position):
                return index

    def get(self, i, j):
        return self.array[i][j]

    def exchange(self, index_a, index_b):
        a_i, a_j = index_a
        b_i, b_j = index_b
        x, y = a_i * 3 + a_j, b_i * 3 + b_j
        self.array[a_i][a_j], self.array[b_i][b_j] = self.array[b_i][b_j], self.array[a_i][a_j]
        # self.pieces[x], self.pieces[y] = self.pieces[y], self.pieces[x]

    def slide(self, i, j):
        _max = self.size - 1

        def up_and_down(index):
            if 0 < index:
                yield index - 1
            if index + 1 < self.size:
                yield index + 1

        for _i in up_and_down(i):
            if self.array[_i][j] is None:
                self.exchange([i, j], [_i, j])
                return

        for _j in up_and_down(j):
            if self.array[i][_j] is None:
                self.exchange([i, j], [i, _j])
                return

    def draw(self):
        for _, piece in self.loop():
            piece.draw()
            piece.draw_rect()

    def reposition(self):
        def xy_iter():
            for y in range(0, self.background_size[1], self.pieces_size[1]):
                for x in range(0, self.background_size[0], self.pieces_size[0]):
                    yield x, y

        for piece, position in zip(self.flatten_array(), xy_iter()):
            if not piece:
                continue
            piece.x, piece.y = position

    def is_finish(self):
        for _, piece in self.loop():  # type: PuzzlePiece
            if piece.origin_x != piece.x or piece.origin_y != piece.y:
                return False
        return True


def main():
    background = PuzzleImage('resource/bg.png')
    background_size = background.image.get_size()
    piece_size = [n // 3 for n in background_size]

    pieces = []
    for y in range(0, background_size[1], piece_size[1]):
        for x in range(0, background_size[0], piece_size[0]):
            pieces.append(PuzzlePiece(crop_image(background.image, x, y, piece_size), x, y))

    del pieces[2]  # 3번째 조각 삭제
    random.shuffle(pieces)
    pieces.insert(2, None)  # 3번째 조각 None 으로 대체

    piece_array = PieceArray(pieces, piece_size, background_size)
    piece_array.reposition()

    # print(type(screen))
    # pieces.append(PuzzlePiece(crop_image(background.image, 0, 0, piece_size), 0, 0))

    def draw(success=False):
        screen.fill(white)
        if not success:
            piece_array.draw()
        else:
            background.draw()

    is_success = False
    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                mouse_pos = pygame.mouse.get_pos()
                index = piece_array.find_hit(mouse_pos)
                if index:
                    piece_array.slide(*index)
                    piece_array.reposition()
                    if piece_array.is_finish():
                        is_success = True

        draw(is_success)
        pygame.display.update()


if __name__ == "__main__":
    main()
