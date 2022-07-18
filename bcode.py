import barcode
import re
import os
from barcode.writer import ImageWriter
from pathlib import Path
from loguru import logger



class CreatePluBarcode:
    def __init__(self) -> None:
        self._data = ''
        self._path_root = Path(os.path.dirname(__file__))
        self.path_bcode = self._path_root / 'plu_barcodes'
        self.bc_file = None
        if not self.path_bcode.exists():
            os.mkdir(self.path_bcode.absolute())


    def set_data(self, data: str) -> None:
        data = re.sub(r'[^\d]', '', data)
        self._data = data
        self.img = {}


    @property
    def data(self) -> str:
        if len(self._data) < 13:
            for x in range(13):
                if len(self._data) == 13: break
                self._data += '0'
        elif len(self._data) > 13:
           return self._data[0:13]
        else:
            return self._data
        return self._data


    def create_ean13(self) -> None:
        if len(self.data) == 0:
            logger.error("Пуста дата скорестуйтесь методом self.set_data")
        else:
            self.bc_file = self.path_bcode / ( self.data + '.png')
            if not self.bc_file.exists():
                self.img = barcode.get('ean13', self.data, writer = ImageWriter())
                self.img.save(self.bc_file.absolute())
            logger.debug('create file: ' + str(self.bc_file.absolute()))


    def gen_data_plu_bcode(self, plu: int, w: float) -> None:
        def get_valid_plu(plu:int) -> str:
            plu = str(plu)
            logger.debug(plu)
            if len(plu) == 4:
                return plu
            elif len(plu) == 3:
                return '0' + plu
            elif len(plu) == 2:
                return '00' + plu
            else:
                return '0000'

        def get_valid_w(w: float) -> str:
            w = str(w)
            w = w.replace('.', '')
            if len(w) == 5:
                return w
            elif len(w) == 4:
                return '0'+w
            else:
                return '00000'

        code = '200'
        code += get_valid_plu(plu)
        code += get_valid_w(w)
        code += '7'
        self.set_data(code)
        self.create_ean13()


    def show(self) -> None:
        self.img.show()


    def get_file_ean13(self):
        return open( str( self.bc_file.absolute() ) +'.png', 'rb')


if __name__ == "__main__":
    data = '4821230000006'
    bc = CreatePluBarcode()
    bc.gen_data_plu_bcode(8726, 0.054)
        
