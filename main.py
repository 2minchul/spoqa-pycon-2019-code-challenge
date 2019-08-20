import random
import sys
from itertools import chain, cycle
from typing import Tuple, Generator, Iterable, Optional, List

import pygame

white = (255, 255, 255)
black = (0, 0, 0)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


class ImageObject:
    x = y = 0
    image: pygame.Surface
    parent: Optional[pygame.Surface]

    def get_position(self):
        return self.x, self.y

    def draw(self):
        if self.parent:
            self.parent.blit(self.image, self.get_position())


class PuzzleImage(ImageObject):
    def __init__(self, path, parent=None):
        self.image: pygame.Surface = pygame.image.load(path).convert_alpha()
        self.parent = parent


Size = Tuple[int, int]  # width, height
Position = Tuple[int, int]  # x, y


class PuzzlePiece(ImageObject):
    def __init__(self, image: pygame.Surface, x: int, y: int, parent: Optional[pygame.Surface] = None):
        self.x = self.origin_x = x
        self.y = self.origin_y = y
        self.image = image
        self.width, self.height = self.image.get_size()
        self.parent = parent

    def draw_rect(self, border: int = 1):
        if self.parent:
            pygame.draw.rect(self.parent, black, [self.x, self.y, *self.image.get_size()], border)

    def is_hit(self, position: Position):
        if self.x <= position[0] < self.x + self.width and self.y <= position[1] < self.y + self.height:
            return True
        return False


PieceArrayIndex = Tuple[int, int]  # i, j
PieceArrayIterItem = Tuple[PieceArrayIndex, PuzzlePiece]
PieceOrNone = Optional[PuzzlePiece]


def crop_image(image: pygame.Surface, position: Position, size: Size):
    cropped = pygame.Surface(size)
    cropped.blit(image, (0, 0), (*position, *size))
    return cropped


class PieceArray:
    array: List[List[PieceOrNone]]
    pieces_size: Size
    background_size: Size
    puzzle_length: int

    def __init__(self, pieces: List[PieceOrNone], pieces_size: Size, background_size: Size, puzzle_length: int = 3):
        self.pieces_size = pieces_size
        self.background_size = background_size
        self.puzzle_length = puzzle_length
        self.array = [i for i in chunks(pieces, self.puzzle_length)]  # 3x3 리스트로 reshape

    def loop(self) -> Generator[PieceArrayIterItem, None, None]:
        for i, pieces in enumerate(self.array):
            for j, piece in enumerate(pieces):
                if piece:  # None 은 건너뛰기
                    yield (i, j), piece

    def flatten_array(self) -> Iterable[PieceOrNone]:
        return chain(*self.array)

    def find_hit(self, position: Position) -> Optional[PieceArrayIndex]:
        for index, piece in self.loop():
            if piece.is_hit(position):
                return index

        return None

    def get(self, i: int, j: int) -> PuzzlePiece:
        return self.array[i][j]

    def exchange(self, index_a: PieceArrayIndex, index_b: PieceArrayIndex):
        a_i, a_j = index_a
        b_i, b_j = index_b
        self.array[a_i][a_j], self.array[b_i][b_j] = self.array[b_i][b_j], self.array[a_i][a_j]

    def slide(self, index: PieceArrayIndex):
        i, j = index

        def up_and_down(n: int) -> Generator[int, None, None]:
            _max = self.puzzle_length - 1
            if 0 < n:
                yield n - 1
            if n < _max:
                yield n + 1

        # for each (i+-1, j) and (i, j+-1)
        for _index in chain(zip(up_and_down(i), cycle([j])),
                            zip(cycle([i]), up_and_down(j))):  # type: PieceArrayIndex
            if self.get(*_index) is None:
                self.exchange(index, _index)
                break

        self.reposition()

    def draw(self):
        for _, piece in self.loop():
            piece.draw()
            piece.draw_rect()

    def reposition(self):
        def position_iter() -> Generator[Position, None, None]:
            for y in range(0, self.background_size[1], self.pieces_size[1]):
                for x in range(0, self.background_size[0], self.pieces_size[0]):
                    yield x, y

        for piece, position in zip(self.flatten_array(), position_iter()):
            if piece is None:
                continue
            piece.x, piece.y = position

    def is_finish(self):
        for _, piece in self.loop():
            if piece.origin_x != piece.x or piece.origin_y != piece.y:
                return False
        return True


def main(background_image_path='resource/bg.png'):
    puzzle_length = 3  # n x n 퍼즐
    background_size: Size = pygame.image.load(background_image_path).get_size()
    piece_size: Size = (background_size[0] // puzzle_length, background_size[1] // puzzle_length)

    pygame.init()
    pygame.display.set_caption("CONNECT THE PYTHONISTAS")
    screen = pygame.display.set_mode(background_size)
    background = PuzzleImage(background_image_path, parent=screen)

    clock = pygame.time.Clock()

    pieces = []
    for y in range(0, background_size[1], piece_size[1]):
        for x in range(0, background_size[0], piece_size[0]):
            pieces.append(
                PuzzlePiece(crop_image(background.image, (x, y), piece_size), x, y, parent=screen)
            )

    del pieces[2]  # 3번째 조각 삭제
    random.shuffle(pieces)
    pieces.insert(2, None)  # 3번째 조각 None 으로 대체

    piece_array = PieceArray(pieces, piece_size, background_size, puzzle_length)
    piece_array.reposition()

    def draw(success=False):
        screen.fill(white)
        if not success:
            piece_array.draw()
        else:
            background.draw()

    is_success = False
    while True:  # main loop
        clock.tick(60)
        for event in pygame.event.get():  # event loop (run forever)
            if event.type == pygame.QUIT:
                sys.exit()

            if not is_success and event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                # 왼쪽 마우스 클릭 이벤트
                mouse_position = pygame.mouse.get_pos()
                index = piece_array.find_hit(mouse_position)
                if index:
                    piece_array.slide(index)
                    if piece_array.is_finish():
                        is_success = True

        draw(is_success)
        pygame.display.update()


if __name__ == "__main__":
    main()
