"""Monta deck_resumo.js = base (identidade, master, componentes) + resumo_body.js (slides do Resultado Geral)"""
import os
A = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(A, "deck_resumo.js"), "w", encoding="utf-8").write(
    open(os.path.join(A, "deck_resumo_base.js"), encoding="utf-8").read() + open(os.path.join(A, "resumo_body.js"), encoding="utf-8").read())
