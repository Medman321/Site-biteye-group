/* Connexion à la base Supabase où l'administration (/admin) enregistre les références et les prestations.
   Laissez les deux valeurs vides : le site affiche alors le contenu intégré à la page.
   Ces deux valeurs sont publiques par nature (Supabase > Project Settings > API) :
   les droits d'écriture sont protégés par la base elle-même, pas par ce fichier. */
window.BITEYE_DB = {
  url: '',  // ex. https://abcdefgh.supabase.co
  cle: ''   // clé « anon public » ou « publishable »
};

/* Connexion future au CRM BitEye : adresse qui reçoit chaque demande du formulaire (POST JSON :
   nom, societe, tel, metier, sujet, langue, page). Vide : les demandes arrivent seulement dans l'administration. */
window.BITEYE_CRM = {
  url: ''
};
