from datetime import datetime, timedelta
import threading
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner

try:
  from plyer import notification
except ImportError:
  pass


class BursaEzanApp(App):

  def build(self):
    self.title = "Bursa Ezan Alarm"
    root = BoxLayout(orientation="vertical", padding=15, spacing=10)

    root.add_widget(
        Label(
            text="📍 Bursa Namaz Vakti & Alarm",
            font_size=20,
            bold=True,
            size_hint_y=None,
            height=40,
        )
    )

    scroll = ScrollView(size_hint=(1, 0.8))
    content_layout = BoxLayout(
        orientation="vertical", size_hint_y=None, spacing=10, padding=5
    )
    content_layout.bind(
        minimum_height=content_layout.setter("height")
    )

    self.vakit_labels = {}
    self.vakit_spinners = {}

    vakitler = [
        ("İmsak (Sabah)", "40"),
        ("Öğle", "10"),
        ("İkindi", "15"),
        ("Akşam", "10"),
        ("Yatsı", "10"),
    ]

    for vakit, varsayilan in vakitler:
      box = BoxLayout(
          orientation="horizontal", size_hint_y=None, height=50, spacing=10
      )
      lbl = Label(
          text=f"{vakit}: Bekleniyor", font_size=14, halign="left", valgn="middle"
      )
      lbl.bind(size=lbl.setter("text_size"))
      self.vakit_labels[vakit] = lbl
      box.add_widget(lbl)

      spinner = Spinner(
          text=f"{varsayilan} dk",
          values=("5 dk", "10 dk", "15 dk", "20 dk", "30 dk", "40 dk"),
          size_hint_x=None,
          width=90,
      )
      self.vakit_spinners[vakit] = spinner
      box.add_widget(spinner)

      content_layout.add_widget(box)

    scroll.add_widget(content_layout)
    root.add_widget(scroll)

    self.lbl_status = Label(
        text="Durum: Vakitler yükleniyor...",
        font_size=13,
        size_hint_y=None,
        height=30,
    )
    root.add_widget(self.lbl_status)

    btn_refresh = Button(
        text="🔄 Vakitleri Güncelle",
        size_hint_y=None,
        height=45,
        background_color=(0.1, 0.6, 0.8, 1),
    )
    btn_refresh.bind(on_press=self.fetch_times)
    root.add_widget(btn_refresh)

    self.bugunku_vakitler = {}
    threading.Thread(target=self.fetch_times, daemon=True).start()
    Clock.schedule_interval(self.check_alarms, 1)

    return root

  def fetch_times(self, *args):
    try:
      url = "https://api.aladhan.com/v1/timingsByCity?city=Bursa&country=Turkey&method=13"
      resp = requests.get(url, timeout=5)
      if resp.status_code == 200:
        timings = resp.json()["data"]["timings"]
        self.bugunku_vakitler = {
            "İmsak (Sabah)": timings.get("Fajr"),
            "Öğle": timings.get("Dhuhr"),
            "İkindi": timings.get("Asr"),
            "Akşam": timings.get("Maghrib"),
            "Yatsı": timings.get("Isha"),
        }
        for v_ad, saat in self.bugunku_vakitler.items():
          if v_ad in self.vakit_labels:
            Clock.schedule_once(
                lambda dt, va=v_ad, s=saat: setattr(
                    self.vakit_labels[va], "text", f"{va}: {s}"
                )
            )
        Clock.schedule_once(
            lambda dt: setattr(
                self.lbl_status, "text", "Durum: Vakitler güncel."
            )
        )
    except Exception as e:
      Clock.schedule_once(
          lambda dt: setattr(self.lbl_status, "text", f"Hata: {str(e)}")
      )

  def check_alarms(self, dt):
    if not self.bugunku_vakitler:
      return
    simdi = datetime.now()
    for vakit_adi, saat in self.bugunku_vakitler.items():
      if not saat:
        continue
      try:
        dakika_str = self.vakit_spinners[vakit_adi].text.split()[0]
        dakika_farki = int(dakika_str)
        v_zaman = datetime.strptime(saat, "%H:%M")
        v_bugun = simdi.replace(
            hour=v_zaman.hour, minute=v_zaman.minute, second=0, microsecond=0
        )
        alarm_zamani = v_bugun - timedelta(minutes=dakika_farki)
        if (
            simdi.hour == alarm_zamani.hour
            and simdi.minute == alarm_zamani.minute
            and simdi.second == 0
        ):
          self.trigger_alarm(vakit_adi, saat, dakika_farki)
      except:
        pass

  def trigger_alarm(self, vakit, saat, dk):
    mesaj = f"Dikkat! {vakit} vaktine {dk} dakika kaldı! ({saat})"
    try:
      notification.notify(title="Ezan Alarmı", message=mesaj, timeout=10)
    except:
      pass


if __name__ == "__main__":
  BursaEzanApp().run()