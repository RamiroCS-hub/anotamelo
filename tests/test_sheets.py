"""
Tests para app/services/sheets.py — Fase 3: delete_expense y search_expenses.

Usa mocks de gspread para no requerir conexión real a Google Sheets.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.models.expense import ParsedExpense
from app.services.sheets import SheetsService


# ---------------------------------------------------------------------------
# Fixture: SheetsService con dependencias mockeadas
# ---------------------------------------------------------------------------

SAMPLE_HEADERS = [
    "Fecha", "Hora", "Monto", "Moneda",
    "Descripción", "Categoría", "Cálculo", "Mensaje Original",
]


@pytest.fixture
def service():
    """Crea SheetsService sin credenciales reales ni conexión a internet."""
    with (
        patch("gspread.authorize"),
        patch("google.oauth2.service_account.Credentials.from_service_account_file"),
        patch.object(SheetsService, "_ensure_users_sheet"),
    ):
        svc = SheetsService()

    mock_spreadsheet = MagicMock()
    svc.spreadsheet = mock_spreadsheet
    return svc, mock_spreadsheet


def _make_worksheet(rows: list[list[str]]) -> MagicMock:
    """Crea un mock de gspread.Worksheet con get_all_values() configurado."""
    ws = MagicMock()
    ws.get_all_values.return_value = rows
    return ws


# ---------------------------------------------------------------------------
# append_expense — retorna índice de fila
# ---------------------------------------------------------------------------


class TestAppendExpense:
    def test_returns_int_on_success(self, service):
        """append_expense debe retornar un entero cuando tiene éxito."""
        svc, mock_spreadsheet = service
        ws = _make_worksheet([SAMPLE_HEADERS])  # solo header
        mock_spreadsheet.worksheet.return_value = ws

        expense = ParsedExpense(
            amount=850.0, description="farmacia", category="Salud",
            currency="ARS", raw_message="850 farmacia",
        )
        result = svc.append_expense("5491123456789", expense)
        assert isinstance(result, int)

    def test_returns_correct_row_index_first_row(self, service):
        """Con solo el header existente, la primera fila de datos va en la fila 2."""
        svc, mock_spreadsheet = service
        ws = _make_worksheet([SAMPLE_HEADERS])  # 1 fila = header
        mock_spreadsheet.worksheet.return_value = ws

        expense = ParsedExpense(
            amount=500.0, description="cafe", category="Comida",
            currency="ARS", raw_message="500 cafe",
        )
        result = svc.append_expense("5491123456789", expense)
        assert result == 2  # fila 1 = header → nueva fila = 2

    def test_returns_correct_row_index_second_row(self, service):
        """Con 1 gasto ya existente, el nuevo gasto va en la fila 3."""
        svc, mock_spreadsheet = service
        ws = _make_worksheet([
            SAMPLE_HEADERS,
            ["2026-02-19", "10:00", "500", "ARS", "farmacia", "Salud", "", "500 farmacia"],
        ])
        mock_spreadsheet.worksheet.return_value = ws

        expense = ParsedExpense(
            amount=850.0, description="uber", category="Transporte",
            currency="ARS", raw_message="850 uber",
        )
        result = svc.append_expense("5491123456789", expense)
        assert result == 3

    def test_calls_append_row(self, service):
        """append_expense debe llamar a ws.append_row con la fila correcta."""
        svc, mock_spreadsheet = service
        ws = _make_worksheet([SAMPLE_HEADERS])
        mock_spreadsheet.worksheet.return_value = ws

        expense = ParsedExpense(
            amount=1200.0, description="supermercado", category="Comida",
            currency="ARS", raw_message="1200 super",
        )
        svc.append_expense("5491123456789", expense)
        ws.append_row.assert_called_once()
        row_arg = ws.append_row.call_args[0][0]
        assert row_arg[2] == 1200.0       # monto
        assert row_arg[4] == "supermercado"  # descripcion
        assert row_arg[5] == "Comida"    # categoria

    def test_returns_zero_on_error(self, service):
        """En caso de excepción, append_expense retorna 0."""
        svc, mock_spreadsheet = service
        mock_spreadsheet.worksheet.side_effect = Exception("Google Sheets error")

        expense = ParsedExpense(
            amount=100.0, description="error", category="Otro",
            currency="ARS", raw_message="100 error",
        )
        result = svc.append_expense("5491123456789", expense)
        assert result == 0

    def test_result_is_truthy_on_success_falsy_on_error(self, service):
        """Compatibilidad con el handler existente que hace `if result:`."""
        svc, mock_spreadsheet = service

        # Éxito
        ws = _make_worksheet([SAMPLE_HEADERS])
        mock_spreadsheet.worksheet.return_value = ws
        expense = ParsedExpense(
            amount=100.0, description="test", category="Otro",
            currency="ARS", raw_message="100 test",
        )
        assert bool(svc.append_expense("5491123456789", expense))  # truthy

        # Error
        mock_spreadsheet.worksheet.side_effect = Exception("error")
        assert not svc.append_expense("5491123456789", expense)    # falsy (0)


# ---------------------------------------------------------------------------
# delete_expense
# ---------------------------------------------------------------------------


class TestDeleteExpense:
    def test_calls_delete_rows_with_correct_index(self, service):
        """delete_expense debe llamar a ws.delete_rows con el índice correcto."""
        svc, mock_spreadsheet = service
        ws = _make_worksheet([SAMPLE_HEADERS])
        mock_spreadsheet.worksheet.return_value = ws

        svc.delete_expense("5491123456789", 3)
        ws.delete_rows.assert_called_once_with(3)

    def test_returns_true_on_success(self, service):
        """delete_expense retorna True cuando tiene éxito."""
        svc, mock_spreadsheet = service
        ws = _make_worksheet([SAMPLE_HEADERS])
        mock_spreadsheet.worksheet.return_value = ws

        result = svc.delete_expense("5491123456789", 2)
        assert result is True

    def test_returns_false_on_error(self, service):
        """delete_expense retorna False si gspread lanza excepción."""
        svc, mock_spreadsheet = service
        ws = MagicMock()
        ws.delete_rows.side_effect = Exception("API error")
        mock_spreadsheet.worksheet.return_value = ws

        result = svc.delete_expense("5491123456789", 2)
        assert result is False

    def test_delete_last_expense_workflow(self, service):
        """Flujo completo: get_recent_expenses(n=1) + delete_expense."""
        svc, mock_spreadsheet = service
        rows = [
            SAMPLE_HEADERS,
            ["2026-02-19", "10:00", "500", "ARS", "farmacia", "Salud", "", "500 farmacia"],
            ["2026-02-19", "12:00", "850", "ARS", "uber", "Transporte", "", "850 uber"],
        ]
        ws = _make_worksheet(rows)
        mock_spreadsheet.worksheet.return_value = ws

        recents = svc.get_recent_expenses("5491123456789", n=1)
        assert len(recents) == 1
        assert recents[0]["descripcion"] == "uber"  # el más reciente (último)

        # El último gasto está en la fila 3 (header=1, farmacia=2, uber=3)
        last_row_index = len(rows)  # = 3
        result = svc.delete_expense("5491123456789", last_row_index)
        ws.delete_rows.assert_called_once_with(3)
        assert result is True


# ---------------------------------------------------------------------------
# search_expenses
# ---------------------------------------------------------------------------


SAMPLE_ROWS = [
    SAMPLE_HEADERS,
    ["2026-02-01", "10:00", "500",  "ARS", "farmacia",  "Salud",      "", "500 farmacia"],
    ["2026-02-15", "12:00", "850",  "ARS", "uber",      "Transporte", "", "850 uber"],
    ["2026-02-18", "15:00", "1200", "ARS", "uber eats", "Comida",     "", "1200 uber eats"],
    ["2026-02-20", "09:00", "200",  "ARS", "cafe",      "Comida",     "", "200 cafe"],
]


class TestSearchExpenses:
    def _setup(self, service, rows=None):
        svc, mock_spreadsheet = service
        ws = _make_worksheet(rows or SAMPLE_ROWS)
        mock_spreadsheet.worksheet.return_value = ws
        return svc

    def test_search_by_query_matches_correct_rows(self, service):
        """search_expenses filtra por texto en descripción (case-insensitive)."""
        svc = self._setup(service)
        result = svc.search_expenses("5491123456789", query="uber")
        assert len(result) == 2
        descriptions = [r["descripcion"].lower() for r in result]
        assert all("uber" in d for d in descriptions)

    def test_search_by_query_case_insensitive(self, service):
        """La búsqueda de texto es case-insensitive."""
        svc = self._setup(service)
        result_lower = svc.search_expenses("5491123456789", query="farmacia")
        result_upper = svc.search_expenses("5491123456789", query="FARMACIA")
        assert len(result_lower) == len(result_upper) == 1

    def test_search_no_query_returns_all(self, service):
        """Sin filtros, retorna todos los gastos."""
        svc = self._setup(service)
        result = svc.search_expenses("5491123456789")
        assert len(result) == 4  # todos menos el header

    def test_search_by_date_from(self, service):
        """date_from filtra gastos anteriores a la fecha."""
        svc = self._setup(service)
        result = svc.search_expenses("5491123456789", date_from="2026-02-15")
        assert len(result) == 3  # 15, 18, 20
        assert all(r["fecha"] >= "2026-02-15" for r in result)

    def test_search_by_date_to(self, service):
        """date_to filtra gastos posteriores a la fecha."""
        svc = self._setup(service)
        result = svc.search_expenses("5491123456789", date_to="2026-02-18")
        assert len(result) == 3  # 01, 15, 18
        assert all(r["fecha"] <= "2026-02-18" for r in result)

    def test_search_by_date_range(self, service):
        """Combinación de date_from y date_to."""
        svc = self._setup(service)
        result = svc.search_expenses(
            "5491123456789", date_from="2026-02-10", date_to="2026-02-18"
        )
        assert len(result) == 2  # 15 y 18
        assert all("2026-02-10" <= r["fecha"] <= "2026-02-18" for r in result)

    def test_search_combined_query_and_dates(self, service):
        """Filtro de texto + rango de fechas combinados."""
        svc = self._setup(service)
        result = svc.search_expenses(
            "5491123456789", query="uber", date_from="2026-02-16"
        )
        assert len(result) == 1
        assert result[0]["descripcion"] == "uber eats"

    def test_result_includes_row_index(self, service):
        """Cada resultado incluye row_index para poder usar delete_expense."""
        svc = self._setup(service)
        result = svc.search_expenses("5491123456789")
        assert all("row_index" in r for r in result)

    def test_row_index_values_are_correct(self, service):
        """Los row_index deben ser 2, 3, 4, 5 (header está en fila 1)."""
        svc = self._setup(service)
        result = svc.search_expenses("5491123456789")
        row_indices = [r["row_index"] for r in result]
        assert row_indices == [2, 3, 4, 5]

    def test_search_no_match_returns_empty_list(self, service):
        """Si no hay coincidencias, retorna lista vacía."""
        svc = self._setup(service)
        result = svc.search_expenses("5491123456789", query="sushi")
        assert result == []

    def test_search_worksheet_not_found_returns_empty(self, service):
        """Si el usuario no tiene hoja, retorna lista vacía sin crash."""
        svc, mock_spreadsheet = service
        import gspread
        mock_spreadsheet.worksheet.side_effect = gspread.WorksheetNotFound
        result = svc.search_expenses("5491000000000", query="uber")
        assert result == []

    def test_monto_is_float(self, service):
        """Los montos en los resultados deben ser float."""
        svc = self._setup(service)
        result = svc.search_expenses("5491123456789")
        assert all(isinstance(r["monto"], float) for r in result)
