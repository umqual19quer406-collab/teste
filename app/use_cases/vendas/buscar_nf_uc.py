from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx
from app.infra.repositories.faturamento_repo import sf2_buscar_por_doc_serie_tx, sd2_itens_por_nf_id_tx


def buscar_nf_por_doc_serie_tx(
    cur,
    usuario: str,
    filial: str,
    doc: str,
    serie: str,
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})

    filial = (filial or "").strip() or "01"
    doc = (doc or "").strip()
    serie = (serie or "").strip()
    if not doc or not serie:
        raise BusinessError("doc e serie são obrigatórios")

    nf = sf2_buscar_por_doc_serie_tx(cur, filial=filial, doc=doc, serie=serie)
    if not nf:
        raise BusinessError("NF não encontrada")
    itens = sd2_itens_por_nf_id_tx(cur, int(nf["ID"]))
    return {"nf": nf, "itens": itens}
