"""Properties list with advanced filters + detail dialog with tabs."""
from __future__ import annotations

from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QPushButton,
                               QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
                               QSpinBox, QCheckBox, QTextEdit, QTabWidget, QLabel, QFileDialog,
                               QSplitter, QGroupBox)
from PySide6.QtCore import Qt
from app.database import models as m
from app.gui.helpers import fill_table, selected_id, confirm, error, success, info, gate
from app.gui.widgets import SearchBar, Gallery
from app.services import property_service as svc
from app.services import platform_service as plat


def _enum_items(enum_cls) -> list[str]:
    return [""] + [e.value for e in enum_cls]


class PropertyDialog(QDialog):
    def __init__(self, ctx, prop_id: int = 0, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.prop_id = prop_id
        self.setWindowTitle("Immobile" if not prop_id else f"Immobile #{prop_id}")
        self.resize(900, 640)
        self.tabs = QTabWidget()
        lay = QVBoxLayout(self)
        lay.addWidget(self.tabs)
        # --- general form ---
        self.form_w = QWidget()
        fl = QFormLayout(self.form_w)
        self.f_code = QLineEdit(); self.f_city = QLineEdit(); self.f_address = QLineEdit()
        self.f_cap = QLineEdit(); self.f_prov = QLineEdit(); self.f_region = QLineEdit()
        self.f_type = QComboBox(); self.f_type.addItems(_enum_items(m.PropertyType))
        self.f_listing = QComboBox(); self.f_listing.addItems(_enum_items(m.ListingType))
        self.f_status = QComboBox(); self.f_status.addItems(_enum_items(m.PropertyStatus))
        self.f_price = QDoubleSpinBox(); self.f_price.setMaximum(1e9); self.f_price.setPrefix("€ ")
        self.f_rent = QDoubleSpinBox(); self.f_rent.setMaximum(1e7); self.f_rent.setPrefix("€ ")
        self.f_surface = QDoubleSpinBox(); self.f_surface.setMaximum(100000)
        self.f_rooms = QSpinBox(); self.f_rooms.setMaximum(60)
        self.f_bed = QSpinBox(); self.f_bed.setMaximum(40)
        self.f_bath = QSpinBox(); self.f_bath.setMaximum(30)
        self.f_owner = QComboBox(); self.f_agent = QComboBox()
        self.f_energy = QComboBox(); self.f_energy.addItems(_enum_items(m.EnergyClass))
        self.f_garage = QCheckBox("Garage"); self.f_parking = QCheckBox("Posto auto")
        self.f_elev = QCheckBox("Ascensore"); self.f_garden = QCheckBox("Giardino")
        self.f_terr = QCheckBox("Terrazza"); self.f_furn = QCheckBox("Arredato")
        for k, w in [("Codice*", self.f_code), ("Città*", self.f_city), ("Indirizzo", self.f_address),
                     ("CAP", self.f_cap), ("Provincia", self.f_prov), ("Regione", self.f_region),
                     ("Tipo", self.f_type), ("Offerta", self.f_listing), ("Stato", self.f_status),
                     ("Prezzo", self.f_price), ("Canone mensile", self.f_rent),
                     ("Superficie mq", self.f_surface), ("Locali", self.f_rooms),
                     ("Camere", self.f_bed), ("Bagni", self.f_bath),
                     ("Proprietario", self.f_owner), ("Agente", self.f_agent),
                     ("Classe energetica", self.f_energy)]:
            fl.addRow(k, w)
        flags = QHBoxLayout()
        for c in (self.f_garage, self.f_parking, self.f_elev, self.f_garden, self.f_terr, self.f_furn):
            flags.addWidget(c)
        fl.addRow("Dotazioni", flags)
        self.tabs.addTab(self.form_w, "Generale")
        # description
        self.f_desc = QTextEdit()
        dw = QWidget(); dl = QVBoxLayout(dw); dl.addWidget(self.f_desc)
        self.tabs.addTab(dw, "Descrizione")
        # photos
        self.gallery = Gallery()
        self.gallery.primary_requested.connect(self._make_primary)
        self.gallery.delete_requested.connect(self._del_photo)
        pw = QWidget(); pl = QVBoxLayout(pw)
        brow = QHBoxLayout()
        b_add = QPushButton("Aggiungi foto"); b_add.clicked.connect(self._add_photo)
        brow.addWidget(b_add); brow.addStretch(1)
        pl.addLayout(brow); pl.addWidget(self.gallery, 1)
        self.tabs.addTab(pw, "Foto")
        # docs / history placeholders filled on load
        self.docs_label = QLabel(); self.hist_list = QLabel()
        self.hist_list.setWordWrap(True)
        for title, w in (("Documenti", self.docs_label), ("Cronologia", self.hist_list)):
            ww = QWidget(); ll = QVBoxLayout(ww); ll.addWidget(w); self.tabs.addTab(ww, title)
        # buttons
        btns = QHBoxLayout()
        b_save = QPushButton("Salva"); b_save.clicked.connect(self._save)
        b_close = QPushButton("Chiudi"); b_close.setObjectName("Ghost"); b_close.clicked.connect(self.reject)
        btns.addStretch(1); btns.addWidget(b_save); btns.addWidget(b_close)
        lay.addLayout(btns)
        self._load_combos()
        if prop_id:
            self._load()

    def _db(self):
        return self.ctx.db()

    def _load_combos(self):
        db = self._db()
        try:
            self._owners = db.query(m.Owner).filter(m.Owner.is_active.is_(True)).all()
            self._agents = db.query(m.Agent).filter(m.Agent.is_active.is_(True)).all()
            self.f_owner.clear(); self.f_owner.addItem("", 0)
            for o in self._owners:
                self.f_owner.addItem(o.display_name, o.id)
            self.f_agent.clear(); self.f_agent.addItem("", 0)
            for a in self._agents:
                self.f_agent.addItem(a.display_name, a.id)
        finally:
            db.close()

    def _collect(self) -> dict:
        return {
            "code": self.f_code.text().strip().upper(), "city": self.f_city.text().strip(),
            "address": self.f_address.text().strip(), "cap": self.f_cap.text().strip(),
            "province": self.f_prov.text().strip(), "region": self.f_region.text().strip(),
            "ptype": self.f_type.currentText() or "apartment",
            "listing": self.f_listing.currentText() or "sale",
            "status": self.f_status.currentText() or "draft",
            "price": float(self.f_price.value()), "monthly_rent": float(self.f_rent.value()),
            "surface": float(self.f_surface.value()), "rooms": int(self.f_rooms.value()),
            "bedrooms": int(self.f_bed.value()), "bathrooms": int(self.f_bath.value()),
            "owner_id": self.f_owner.currentData() or None,
            "agent_id": self.f_agent.currentData() or None,
            "energy_class": self.f_energy.currentText() or "G",
            "garage": self.f_garage.isChecked(), "parking": self.f_parking.isChecked(),
            "elevator": self.f_elev.isChecked(), "garden": self.f_garden.isChecked(),
            "terrace": self.f_terr.isChecked(), "furnished": self.f_furn.isChecked(),
            "description": self.f_desc.toPlainText(),
        }

    def _load(self):
        db = self._db()
        try:
            p = db.get(m.Property, self.prop_id)
            if not p:
                return
            self.f_code.setText(p.code); self.f_city.setText(p.city); self.f_address.setText(p.address or "")
            self.f_cap.setText(p.cap or ""); self.f_prov.setText(p.province or ""); self.f_region.setText(p.region or "")
            self.f_type.setCurrentText(p.ptype.value); self.f_listing.setCurrentText(p.listing.value)
            self.f_status.setCurrentText(p.status.value)
            self.f_price.setValue(p.price or 0); self.f_rent.setValue(p.monthly_rent or 0)
            self.f_surface.setValue(p.surface or 0); self.f_rooms.setValue(p.rooms or 0)
            self.f_bed.setValue(p.bedrooms or 0); self.f_bath.setValue(p.bathrooms or 0)
            self.f_energy.setCurrentText(p.energy_class.value)
            for chk, val in ((self.f_garage, p.garage), (self.f_parking, p.parking),
                             (self.f_elev, p.elevator), (self.f_garden, p.garden),
                             (self.f_terr, p.terrace), (self.f_furn, p.furnished)):
                chk.setChecked(bool(val))
            self.f_desc.setPlainText(p.description or "")
            if p.owner_id:
                i = self.f_owner.findData(p.owner_id)
                if i >= 0:
                    self.f_owner.setCurrentIndex(i)
            if p.agent_id:
                i = self.f_agent.findData(p.agent_id)
                if i >= 0:
                    self.f_agent.setCurrentIndex(i)
            imgs = db.query(m.PropertyImage).filter(
                m.PropertyImage.property_id == p.id).order_by(m.PropertyImage.sort_order).all()
            self.gallery.set_images([(im.id, im.thumb_path or im.file_path, im.is_primary) for im in imgs])
            docs = plat.list_documents(db, "property", p.id)
            self.docs_label.setText("\n".join(
                f"• {d.original_name} ({d.category})" for d in docs) or "Nessun documento (vedi pagina Documenti)")
            logs = db.query(m.AuditLog).filter(m.AuditLog.entity == "property",
                                               m.AuditLog.entity_id == str(p.id)).order_by(
                m.AuditLog.id.desc()).limit(30).all()
            self.hist_list.setText("\n".join(
                f"{l.at:%d/%m/%Y %H:%M} {l.username} {l.action}" for l in logs) or "Nessuna attività")
        finally:
            db.close()

    def _save(self):
        db = self._db()
        try:
            user = self.ctx.current_user()
            data = self._collect()
            if not data["code"] or not data["city"]:
                error(self, "Codice e città obbligatori"); return
            if self.prop_id:
                svc.update_property(db, user, self.prop_id, data)
            else:
                obj = svc.create_property(db, user, data)
                self.prop_id = obj.id
            success(self, "Immobile salvato")
            self.accept()
        except Exception as e:
            try:
                db.rollback()
            except Exception:
                pass
            error(self, str(e))
        finally:
            db.close()

    def _add_photo(self):
        if not self.prop_id:
            info(self, "Salva prima l'immobile"); return
        f, _ = QFileDialog.getOpenFileName(self, "Seleziona immagine",
                                           "", "Immagini (*.jpg *.jpeg *.png *.webp)")
        if not f:
            return
        db = self._db()
        try:
            svc.add_photo(db, self.ctx.current_user(), self.prop_id, f)
            self._load()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _make_primary(self, img_id: int):
        db = self._db()
        try:
            svc.set_primary_photo(db, self.ctx.current_user(), img_id)
            self._load()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _del_photo(self, img_id: int):
        if not confirm(self, "Eliminare la foto?"):
            return
        db = self._db()
        try:
            svc.delete_photo(db, self.ctx.current_user(), img_id)
            self._load()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()


class PropertiesPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Immobili</b>"))
        self.search = SearchBar("Cerca codice, città, indirizzo, CAP...")
        self.search.searched.connect(lambda _t: self.refresh())
        lay.addWidget(self.search)
        filt = QHBoxLayout()
        self.f_city = QLineEdit(); self.f_city.setPlaceholderText("Città")
        self.f_type = QComboBox(); self.f_type.addItems([""] + [e.value for e in m.PropertyType])
        self.f_listing = QComboBox(); self.f_listing.addItems([""] + [e.value for e in m.ListingType])
        self.f_status = QComboBox(); self.f_status.addItems([""] + [e.value for e in m.PropertyStatus])
        self.f_pmin = QLineEdit(); self.f_pmin.setPlaceholderText("Prezzo min")
        self.f_pmax = QLineEdit(); self.f_pmax.setPlaceholderText("Prezzo max")
        self.f_furn = QCheckBox("Arredato"); self.f_garage = QCheckBox("Garage")
        for w in (self.f_city, self.f_type, self.f_listing, self.f_status,
                  self.f_pmin, self.f_pmax, self.f_furn, self.f_garage):
            filt.addWidget(w)
        b_f = QPushButton("Filtra"); b_f.clicked.connect(self.refresh)
        filt.addWidget(b_f)
        lay.addLayout(filt)
        btns = QHBoxLayout()
        self.b_new = QPushButton("Nuovo"); self.b_new.clicked.connect(self._new)
        self.b_edit = QPushButton("Apri / Modifica"); self.b_edit.clicked.connect(self._edit)
        self.b_del = QPushButton("Archivia"); self.b_del.setObjectName("Danger")
        self.b_del.clicked.connect(self._delete)
        btns.addWidget(self.b_new); btns.addWidget(self.b_edit); btns.addWidget(self.b_del)
        btns.addStretch(1)
        lay.addLayout(btns)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(lambda *_: self._edit())
        lay.addWidget(self.table, 1)
        self._apply_perms()

    def _apply_perms(self):
        gate(self.b_new, self.ctx.can("properties.create"))
        gate(self.b_edit, self.ctx.can("properties.view"))
        gate(self.b_del, self.ctx.can("properties.delete"))

    def _filters(self) -> dict:
        def num(w):
            try:
                return float(w.text()) if w.text().strip() else None
            except ValueError:
                return None
        return {"text": self.search.edit.text().strip(), "city": self.f_city.text().strip(),
                "ptype": self.f_type.currentText(), "listing": self.f_listing.currentText(),
                "status": self.f_status.currentText(), "price_min": num(self.f_pmin),
                "price_max": num(self.f_pmax),
                "furnished": self.f_furn.isChecked(), "garage": self.f_garage.isChecked()}

    def refresh(self) -> None:
        self._apply_perms()
        db = self.ctx.db()
        try:
            rows, _total = svc.search_properties(db, self._filters(), limit=300)
            fill_table(self.table, ["ID", "Codice", "Tipo", "Città", "Prezzo", "Mq", "Stato"],
                       [[p.id, p.code, p.ptype.value, p.city, f"{p.price:,.0f}",
                         p.surface, p.status.value] for p in rows],
                       ids=[p.id for p in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _new(self):
        if PropertyDialog(self.ctx, 0, self).exec():
            self.refresh()

    def _edit(self):
        pid = selected_id(self.table)
        if pid is None:
            info(self, "Seleziona un immobile"); return
        if PropertyDialog(self.ctx, pid, self).exec():
            self.refresh()

    def _delete(self):
        pid = selected_id(self.table)
        if pid is None:
            return
        if not confirm(self, "Archiviare l'immobile (soft-delete)?"):
            return
        db = self.ctx.db()
        try:
            svc.archive_property(db, self.ctx.current_user(), pid)
            success(self, "Immobile archiviato")
            self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()
