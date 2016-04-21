#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# bormeparser.backends.seccion_c.basic.parser.py -
# Copyright (C) 2016 Pablo Castellano <pablo@anche.no>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from bormeparser.backends.base import BormeCParserBackend
from lxml import etree

import datetime
import logging
import re
import six

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)


class LxmlBormeCParser(BormeCParserBackend):
    """
    BORME C Parser using lxml and regular expressions
    """
    def __init__(self, filename, log_level=logging.WARN):
        super(LxmlBormeCParser, self).__init__(filename)
        logger.setLevel(log_level)

    def _clean_cif(self, companies):
        cifs = []
        for cif in companies:
            cif = cif.replace('.', '').replace('-', '')
            cifs.append(cif)
        return cifs

    def parse(self):
        if six.PY2:
            content = open(self.filename).read()
        else:
            content = open(self.filename, 'r', encoding='iso-8859-1').read()

        if content.startswith('<?xml'):
            return self._parse_xml()
        elif content.startswith('<!DOCTYPE HTML PUBLIC'):
            return self._parse_html(content)
        else:
            raise ValueError('Cannot detect BORME C type')

    def _parse_xml(self):
        tree = etree.parse(self.filename)

        texto = tree.xpath('/documento/texto/p/text()')
        empresa = tree.xpath('/documento/metadatos/titulo/text()')[0]                       # "DESARROLLOS ESPECIALES DE SISTEMAS DE ANCLAJE, S.A."
        diario_numero = tree.xpath('/documento/metadatos/diario_numero/text()')[0]          # "101"
        departamento = tree.xpath('/documento/metadatos/departamento/text()')[0]            # "CONVOCATORIAS DE JUNTAS"
        numero_anuncio = tree.xpath('/documento/metadatos/numero_anuncio/text()')[0]        # "44738"
        id_anuncio = tree.xpath('/documento/metadatos/id_anuncio/text()')[0]                # "A110044738"
        fecha_publicacion = tree.xpath('/documento/metadatos/fecha_publicacion/text()')[0]  # "20110527"
        pagina_inicial = tree.xpath('/documento/metadatos/pagina_inicial/text()')[0]        # "22110"
        pagina_final = tree.xpath('/documento/metadatos/pagina_final/text()')[0]            # "22116"
        cve = tree.xpath('/documento/metadatos/identificador/text()')[0]                    # "BORME-C-2011-20488"

        texto = '\n\n'.join(texto)
        fecha_publicacion = datetime.datetime.strptime(fecha_publicacion, '%Y%m%d').date()

        cifs = re.findall('(?:[CN]IF n\w+|[CN]IF) ([A-Z]-?[\d.-]+)', texto)
        cifs = self._clean_cif(cifs)

        return {'departamento': departamento,
                'texto': texto,
                'diario_numero': diario_numero,
                'numero_anuncio': numero_anuncio,
                'id_anuncio': id_anuncio,
                'pagina_inicial': pagina_inicial,
                'pagina_final': pagina_final,
                'fecha': fecha_publicacion,
                'empresa': empresa,
                'cifs': cifs,
                'cve': cve
                }

    def _parse_html(self, content):
        html = etree.HTML(content)

        body = html.xpath('//div[@id="contenedor"][1]')[0]
        empresa = body.xpath('//p[@class="documento-tit"]/text()')[0]  # TODO: Partir por los intros y borrar lo que haya entre paréntesis
        texto = '\n\n'.join(body.xpath('//div[@id="textoxslt"]/p/text()'))
        title = body.xpath('//div[@class="poolBdatos"]/h3/text()[1]')[0]  # "CONVOCATORIAS DE JUNTAS (BORME 101 de 27/5/2011)"
        title_groups = re.search('(.*) \(BORME (\d+) de (\d+)/(\d+)/(\d+)\)', title)
        departamento, diario_numero = title_groups.group(1), title_groups.group(2)
        fecha_publicacion = datetime.date(int(title_groups.group(5)), int(title_groups.group(4)), int(title_groups.group(3)))

        cve = html.xpath('//div[@class="contMigas"]/ul/li[@class="destino"]/text()')[0]  # "Documento BORME-C-2011-20488"
        cve = cve.split()[1]

        cifs = re.findall('(?:[CN]IF n\w+|[CN]IF) ([A-Z]-?[\d.-]+)', texto)
        cifs = self._clean_cif(cifs)

        return {'departamento': departamento,
                'texto': texto,
                'diario_numero': diario_numero,
                'fecha': fecha_publicacion,
                'empresa': empresa,
                'cifs': cifs,
                'cve': cve
                }


if __name__ == '__main__':
    import pprint
    borme = LxmlBormeCParser('examples/BORME-C-2011-20488.html').parse()
    pprint.pprint(borme, width=160)
    print('\n------------------------------------------------------\n')
    borme = LxmlBormeCParser('examples/BORME-C-2011-20488.xml').parse()
    pprint.pprint(borme, width=160)