# CDE Copper translations

All theme QML uses the gettext domain `cde-copper`. Run these commands from
`CDE/` with GNU gettext installed to update the template and existing catalogs:

```sh
xgettext -C --from-code=UTF-8 -k \
  -ki18nd:2 -ki18ndc:2c,3 -ki18ndp:2,3 -kI18N_NOOP:1 \
  --flag=i18nd:2:kde-format --flag=i18ndp:2:kde-format --flag=i18ndp:3:kde-format \
  --package-name=cde-copper --package-version=0.9.5 \
  -o po/cde-copper.pot \
  frontpanel/contents/ui/*.qml frontpanel/contents/ui/launch.js \
  frontpanel/contents/config/config.qml backdrop/contents/ui/config.qml \
  lookandfeel/contents/splash/Splash.qml lookandfeel/contents/logout/Logout.qml \
  shell/contents/lockscreen/LockScreen.qml
for catalog in po/*.po; do
  msgmerge --update --backup=none "$catalog" po/cde-copper.pot
done
msgfmt --check --statistics -o /tmp/cde-copper-de.mo po/de.po
```

Resolve new or fuzzy entries before shipping. Preserve `%1`, `%2`, and any
accelerators; translate whole sentences, using `i18ndp` for plurals. Palette,
backdrop, application, and system workspace names remain unchanged. User-defined
starter labels remain unchanged. `launch.js` is a `.pragma library`: its
`I18N_NOOP` list marks messages for extraction, and QML supplies the translation
callback for notifications and translates preset/menu text at presentation time.
Keep that list in sync with new library messages.

To add a language (replace `fr` with its language code):

```sh
msginit --input=po/cde-copper.pot --locale=fr --output-file=po/fr.po
```

Translate every entry, set the language's `Plural-Forms` header, remove reviewed
fuzzy flags, and check with `msgfmt --check`. Catalogs must use UTF-8.

`i18n.compile_translations(out_dir)` compiles every `po/*.po` into
`out_dir/locale/<lang>/LC_MESSAGES/cde-copper.mo`. It uses `msgfmt` when available,
otherwise a dependency-free Python compiler supporting multiline entries,
contexts, and plurals (fuzzy entries are omitted). Example from `CDE/`:

```sh
python3 -c 'from i18n import compile_translations; compile_translations("build")'
```

KDE's `KLocalizedString` searches `locale/` below every XDG data directory for
`<domain>.mo`. The user installation must therefore place the German catalog at
`~/.local/share/locale/de/LC_MESSAGES/cde-copper.mo` (or the corresponding
`$XDG_DATA_HOME/locale/` directory), rather than inside the plasmoid or theme
package. Build and installation wiring is handled separately.
