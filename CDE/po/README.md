# CDE Copper translations

All theme QML uses the gettext domain `cde-copper`. Run this from `CDE/` with GNU
gettext installed to update the template and existing catalogs:

```sh
python3 po/update.py            # or --check: only report messages that would be lost
msgfmt --check --statistics -o /dev/null po/de.po
```

xgettext only finds literal `i18nd()` calls. Messages looked up by a variable, the
backdrop names and picture titles, are kept by hand in `po/names.pot`; merging
without them would drop their translations.

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
