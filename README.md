# Weekly Cleaning (Streamlit)

Barista bur 7 honogt 4 tseverlgee random avna, ali ch udur hiij bolno. Zurag oruulahad ✓ bolno.
7 honog duusahad hiigeegui hunuusiin jagsaalt garch, ugugdul automataar tsewerlegdeed shine 7 honog ehelne.

## Deploy (tuluh uneguи)
1. **Supabase**: supabase.com -> New project. SQL Editor deer `supabase_setup.sql`-iin utgiig ajilluulna.
   Project Settings -> API deer `Project URL` ba `service_role` key-g huulna.
2. **GitHub**: shine (private) repository uusgeed ene folder-iin buh file-iig upload hiine
   (`.streamlit/secrets.toml` upload hiih BUUR).
3. **Streamlit Community Cloud**: share.streamlit.io -> GitHub-aar nevtreed "Create app" -> repo, branch,
   Main file = `app.py`. Advanced settings -> Secrets deer `secrets.toml.example`-iin utgiig uuriin utgaar bichij hulguulna.
4. Garch irsen link-ee baristanuudad ilgeene. Nevtreh shaardlagagui. Admin: zuun taliin tsesnees nuuts ugeer nevtrene.

## Local turshilt
    pip install -r requirements.txt
    streamlit run app.py     # secrets baihgui bol local_store.json deer hadgalna
