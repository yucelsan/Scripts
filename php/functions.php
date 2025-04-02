<?php

// Crétaion de plugin PHP pour le site YUCELSAN
// Développement sur mesure
// AUTHOR : SERDAR AYSAN
// COMPANY : YUCELSAN SAS
// CODE : PHP / THEME : VAXIMO

function vaximo_enqueue_style() {
    wp_enqueue_style( "parent-style" , get_parent_theme_file_uri( "/style.css" ) );
}
add_action( 'wp_enqueue_scripts', 'vaximo_enqueue_style' );

function detect_user_city() {
    $user_ip = $_SERVER['REMOTE_ADDR']; // Récupérer l'IP de l'utilisateur
    $geo_api_url = "http://ip-api.com/json/$user_ip"; // API de géolocalisation
    $geo_data = wp_remote_get($geo_api_url); // Requête vers l'API

    if (is_wp_error($geo_data)) {
        return " votre région"; // Valeur par défaut si l'API échoue
    }

    $geo_body = wp_remote_retrieve_body($geo_data);
    $geo_info = json_decode($geo_body);

    if (isset($geo_info->city)) {
        return esc_html($geo_info->city);
    } else {
        return " votre région"; // Valeur par défaut si pas de ville trouvée
    }
}

// Création du shortcode [user_city]
function user_city_shortcode() {
    return detect_user_city();
}
add_shortcode('user_city', 'user_city_shortcode');

////////////////////////// FORMULAIRE CANDIDATURE SPONTANEE PAGE TEAM  ///////////////////////////////////////////////////////////////////

function yucelsan_cv_upload_form() {
    ob_start();
    ?>
    <form class="yucelsan-cv-form" action="<?php echo esc_url($_SERVER['REQUEST_URI']); ?>" method="post" enctype="multipart/form-data">
        <label>Nom et prénom :</label>
        <input type="text" name="name" required>
        
        <label>Email :</label>
        <input type="email" name="email" required>
        
        <label>Numéro de téléphone :</label>
        <input type="text" name="phone" required>

        <label>Message :</label>
        <textarea name="message"></textarea>
        
        <label>Déposer votre CV (PDF ou Word) :</label>
        <input type="file" name="cv_file" accept=".pdf,.doc,.docx" required>

        <input type="submit" name="submit_cv" value="Envoyer">
    </form>
    <?php
    return ob_get_clean();
}
add_shortcode('yucelsan_cv_form', 'yucelsan_cv_upload_form');

function handle_cv_submission() {
    if (isset($_POST['submit_cv'])) {
        $uploads_dir = wp_upload_dir();
        $upload_path = $uploads_dir['path'];
        
        if (!empty($_FILES['cv_file']['name'])) {
            $allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
            
            if (in_array($_FILES['cv_file']['type'], $allowed_types)) {
                $file_name = sanitize_file_name($_FILES['cv_file']['name']);
                $destination = $upload_path . '/' . $file_name;

                if (move_uploaded_file($_FILES['cv_file']['tmp_name'], $destination)) {
                    $to = 'contact@yucelsan.fr';
                    $subject = "Nouveau CV YUCELSAN FR reçu";
                    $message = "Nom: " . sanitize_text_field($_POST['name']) . "\nEmail: " . sanitize_email($_POST['email']) . "\nTéléphone: " . sanitize_text_field($_POST['phone']) . "\nMessage: " . sanitize_textarea_field($_POST['message']);
                    $headers = [
                        "From: noreply@yucelsan.fr",
                        "Content-Type: text/plain; charset=UTF-8"
                    ];

                    // Attacher le fichier au mail
                    $attachments = [$destination];

                    // Envoi du mail avec pièce jointe
                    $mail_sent = wp_mail($to, $subject, $message, $headers, $attachments);

                    if ($mail_sent) {
                        wp_redirect(home_url('/')); // Redirection après soumission
                        exit;
                	} 
				 } 
				else {
                    echo "<p>Erreur lors du téléchargement du fichier.</p>";
                }
            } else {
                echo "<p>Format de fichier non autorisé.</p>";
            }
        }
    }
}
add_action('init', 'handle_cv_submission'); // Correction : init pour éviter 404

////////////////////////////////////// CUSTOM POST TYPE OFFRE D'EMPLOI ADMIN WORDPRESS ////////////////////////////////////////////////////////

function yucelsan_register_job_post_type() {
    $args = array(
        'labels' => array(
            'name' => 'Offres d\'Emploi',
            'singular_name' => 'Offre d\'Emploi',
            'add_new' => 'Ajouter une offre',
            'add_new_item' => 'Ajouter une nouvelle offre',
            'edit_item' => 'Modifier l\'offre',
            'new_item' => 'Nouvelle offre',
            'view_item' => 'Voir l\'offre',
            'search_items' => 'Rechercher une offre',
            'not_found' => 'Aucune offre trouvée',
            'not_found_in_trash' => 'Aucune offre trouvée dans la corbeille',
        ),
        'public' => true,
        'has_archive' => true,
        'supports' => array('title', 'editor', 'thumbnail'),
        'menu_icon' => 'dashicons-businessman',
    );
    register_post_type('offres_emploi', $args);
}
add_action('init', 'yucelsan_register_job_post_type');

/////////////////////////////////////  TABLEAU DE BORD WORDPRESS [CANDIDATURES]  /////////////////////////////////////////////////////////

function yucelsan_register_candidature_post_type() {
    $args = array(
        'labels' => array(
            'name' => 'Candidatures',
            'singular_name' => 'Candidature',
            'menu_name' => 'Candidatures',
            'add_new' => 'Ajouter une candidature',
            'add_new_item' => 'Ajouter une nouvelle candidature',
            'edit_item' => 'Modifier la candidature',
            'new_item' => 'Nouvelle candidature',
            'view_item' => 'Voir la candidature',
            'search_items' => 'Rechercher une candidature',
            'not_found' => 'Aucune candidature trouvée',
        ),
        'public' => false,
        'show_ui' => true,
        'show_in_menu' => true,
        'menu_icon' => 'dashicons-id',
        'supports' => array('title', 'editor', 'custom-fields'),
    );
    register_post_type('candidature', $args);
}
add_action('init', 'yucelsan_register_candidature_post_type');

// Ajouter des colonnes personnalisées dans la liste des candidatures
function yucelsan_candidature_columns($columns) {
    $columns['job_offer'] = 'Offre d\'Emploi';
    $columns['cv'] = 'CV';
    return $columns;
}
add_filter('manage_candidature_posts_columns', 'yucelsan_candidature_columns');

// Remplir les colonnes avec les données
function yucelsan_candidature_custom_column($column, $post_id) {
    if ($column == 'job_offer') {
        echo get_post_meta($post_id, 'job_title', true);
    }
    if ($column == 'cv') {
        $cv_url = get_post_meta($post_id, 'cv_file', true);
        if ($cv_url) {
            echo "<a href='$cv_url' target='_blank'>Télécharger</a>";
        } else {
            echo "Aucun CV";
        }
    }
}
add_action('manage_candidature_posts_custom_column', 'yucelsan_candidature_custom_column', 10, 2);

// Ajouter une metabox avec les détails de la candidature
function yucelsan_candidature_metabox() {
    add_meta_box(
        'candidature_details',
        'Détails de la Candidature',
        'yucelsan_candidature_details_callback',
        'candidature',
        'normal',
        'high'
    );
}
add_action('add_meta_boxes', 'yucelsan_candidature_metabox');

// Afficher les détails dans l'admin
function yucelsan_candidature_details_callback($post) {
    echo "<p><strong>Nom :</strong> " . get_the_title($post->ID) . "</p>";
    echo "<p><strong>Email :</strong> " . get_post_meta($post->ID, 'email', true) . "</p>";
    echo "<p><strong>Téléphone :</strong> " . get_post_meta($post->ID, 'phone', true) . "</p>";
    echo "<p><strong>Offre d'emploi :</strong> " . get_post_meta($post->ID, 'job_title', true) . "</p>";
    echo "<p><strong>Message :</strong><br>" . get_post_meta($post->ID, 'message', true) . "</p>";

    $cv_url = get_post_meta($post->ID, 'cv_file', true);
    if ($cv_url) {
        echo "<p><a href='$cv_url' target='_blank' class='button button-primary'>Télécharger le CV</a></p>";
    } else {
        echo "<p>Aucun CV</p>";
    }
}

/////////////////////////////////////  FORMULAIRE POSTULER [OFFRE D'EMPLOI]  /////////////////////////////////////////////////////////

function yucelsan_candidat_upload_form() {
    ob_start();
    ?>
    <form class="yucelsan-cv-form" action="<?php echo esc_url($_SERVER['REQUEST_URI']); ?>" method="post" enctype="multipart/form-data">
        <label>Nom et prénom :</label>
        <input type="text" name="name" required>
        
        <label>Email :</label>
        <input type="email" name="email" required>
        
        <label>Numéro de téléphone :</label>
        <input type="text" name="phone" required>

        <label>Message :</label>
        <textarea name="message"></textarea>
        
        <label>Déposer votre CV (PDF ou Word) :</label>
        <input type="file" name="cv_file" accept=".pdf,.doc,.docx" required>
		
        <!-- Champ caché pour stocker l’ID et le titre de l'offre -->
        <input type="hidden" id="job-id" name="job_id" value="<?php echo isset($_GET['job_id']) ? esc_attr($_GET['job_id']) : ''; ?>">
		<!--<input type="hidden" id="job-title" name="job_title" value="<?php // echo isset($_GET['job_title']) ? esc_attr(htmlspecialchars($_GET['job_title'], ENT_QUOTES)) : ''; ?>"> -->
		<input type="hidden" id="job-title" name="job_title" value="<?php echo esc_attr(get_the_title(get_queried_object_id())); ?>">
		
        <input type="submit" name="submit_candidat" value="Envoyer">
    </form>
    <?php
    return ob_get_clean();
}
add_shortcode('yucelsan_candidat_form', 'yucelsan_candidat_upload_form');

function handle_candidat_submission() {
    if (isset($_POST['submit_candidat'])) {
        $uploads_dir = wp_upload_dir();
        $upload_path = $uploads_dir['path'];
		
        $job_id = isset($_POST['job_id']) ? sanitize_text_field($_POST['job_id']) : 'Aucune offre spécifiée';
        $job_title = isset($_POST['job_title']) ? sanitize_text_field($_POST['job_title']) : 'Non spécifié';
        $name = sanitize_text_field($_POST['name']);
        $email = sanitize_email($_POST['email']);
        $phone = sanitize_text_field($_POST['phone']);
        $message = sanitize_textarea_field($_POST['message']);

        // 1. CRÉER LA CANDIDATURE DANS WORDPRESS
        $candidature_post = array(
            'post_title'   => $name . " - " . $job_title,
            'post_content' => "Nom : " . $name . "\n\n" .
                              "Email : " . $email . "\n\n" .
                              "Téléphone : " . $phone . "\n\n" .
                              "Offre d'emploi : " . $job_title . "\n\n" .
                              "Message : " . $message,
            'post_status'  => 'publish',
            'post_type'    => 'candidature',
        );

        $candidature_id = wp_insert_post($candidature_post);

        // 2. UPLOAD & STOCKAGE DU CV
        $cv_url = "";
        if (!empty($_FILES['cv_file']['name'])) {
            $file = $_FILES['cv_file'];
            $allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];

            if (in_array($file['type'], $allowed_types)) {
                $file_name = sanitize_file_name($file['name']);
                $destination = $upload_path . '/' . $file_name;

                if (move_uploaded_file($file['tmp_name'], $destination)) {
                    $cv_url = esc_url_raw($uploads_dir['url'] . '/' . $file_name);

                    // STOCKER LE CV DANS WORDPRESS
                    update_post_meta($candidature_id, 'cv_file', $cv_url);
					// Enregistrer les champs en tant que post_meta pour éviter les valeurs vides
					update_post_meta($candidature_id, 'email', $email);
					update_post_meta($candidature_id, 'phone', $phone);
					update_post_meta($candidature_id, 'job_title', $job_title);
					update_post_meta($candidature_id, 'message', $message);
                    error_log("CV enregistré avec succès : " . $cv_url);
                } else {
                    error_log("Erreur lors du téléchargement du fichier.");
                }
            } else {
                error_log("Format de fichier non autorisé : " . $file['type']);
            }
        }

        // 3. ENVOYER UN EMAIL AVEC LE CV EN ATTACHMENT
        $to = 'contact@yucelsan.fr';
        $subject = "Candidature reçue pour $job_title";
        $email_message = "Nom: " . $name . "\n"
                       . "Email: " . $email . "\n"
                       . "Téléphone: " . $phone . "\n"
                       . "Offre d'emploi: " . $job_title . "\n"
                       . "Message: " . $message . "\n"
                       . "CV : " . ($cv_url ? $cv_url : "Aucun CV joint");

        $headers = [
            "From: noreply@yucelsan.fr",
            "Content-Type: text/plain; charset=UTF-8"
        ];

        $attachments = [];
        if ($cv_url) {
            $attachments[] = $upload_path . '/' . $file_name;
        }

        $mail_sent = wp_mail($to, $subject, $email_message, $headers, $attachments);

        // 4. REDIRECTION APRÈS ENVOI DU MAIL
        if ($mail_sent) {
            wp_redirect(home_url('/')); // Redirige vers la page "ACCUEIL"
            exit;
        } else {
            error_log("Erreur lors de l'envoi de l'email.");
            echo "<p>Erreur lors de l'envoi de la candidature.</p>";
        }
    }
}
add_action('init', 'handle_candidat_submission');

/////////////////////////////////////   Page pour afficher toutes les offres d'emploi shortcode [yucelsan_jobs]   /////////////////////////////////////////////////////////

function yucelsan_display_job_offers() {
    ob_start();

    $args = array(
        'post_type'      => 'offres_emploi',
        'posts_per_page' => -1, // Affiche toutes les offres
        'order'          => 'DESC',
    );

    $query = new WP_Query($args);

    if ($query->have_posts()) :
        echo '<div class="job-listings">';
        while ($query->have_posts()) : $query->the_post();
            ?>
            <div class="job-offer">
                <h2><?php the_title(); ?></h2>
                <p><?php the_content(); ?></p>
                <button class="postuler-btn" data-job-id="<?php echo get_the_ID(); ?>" data-job-title="<?php the_title(); ?>">Postuler</button>
            </div>
            <?php
        endwhile;
        echo '</div>';
        wp_reset_postdata();
    else :
        echo "<p>Aucune offre d'emploi disponible pour le moment.</p>";
    endif; ?>
<!-- Formulaire de candidature (caché par défaut) -->
<div id="job-apply-form" style="display: none;">
    <h2>Postuler pour <span id="job-title"></span></h2>
    <?php echo do_shortcode('[yucelsan_candidat_form]'); ?>
    <input type="hidden" id="job-id" name="job_id">
</div>

<script>
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".postuler-btn").forEach(button => {
        button.addEventListener("click", function() {
            let jobTitle = this.getAttribute("data-job-title");
            let jobId = this.getAttribute("data-job-id");

            document.getElementById("job-title").innerText = jobTitle;
            document.getElementById("job-id").value = jobId;
            document.getElementById("job-apply-form").style.display = "block";
        });
    });
});
</script>
	<?php
    return ob_get_clean();
}
add_shortcode('yucelsan_jobs', 'yucelsan_display_job_offers');

function cf7_capture_ip($form_tag) {
    if ($form_tag['name'] === 'submitter_ip') {
        $form_tag['values'][] = $_SERVER['REMOTE_ADDR'];
    }
    return $form_tag;
}
add_filter('wpcf7_form_tag', 'cf7_capture_ip', 10, 1);

/*
function block_spammer_ip() {
    $banned_ips = ['']; // Ajoute d'autres IPs si besoin

    if (in_array($_SERVER['REMOTE_ADDR'], $banned_ips)) {
        wp_die("Accès refusé.");
    }
}
add_action('init', 'block_spammer_ip');
**/

////////////////////////////////////////   CONVERTISSEUR DE CV PDF AU FORMAT JSON   //////////////////////////////////////////////////////

/**
 * Plugin WordPress - Convertisseur de CV PDF en JSON
 */

// Inclure PDFParser manuellement si Composer n'est pas disponible

$autoload_path = ABSPATH . 'wp-content/plugins/pdfparser-lib/pdfparser/autoload.php';
$parser_path = ABSPATH . 'wp-content/plugins/pdfparser-lib/pdfparser/src/Smalot/PdfParser/Parser.php';
$tcpdf_path = ABSPATH . 'wp-content/plugins/pdfparser-lib/tcpdf/tcpdf.php';
require_once ABSPATH . 'wp-content/plugins/pdfparser-lib/pdfparser/src/Smalot/PdfParser/Config.php';
require_once ABSPATH . 'wp-content/plugins/pdfparser-lib/pdfparser/src/Smalot/PdfParser/RawData/RawDataParser.php';
require_once ABSPATH . 'wp-content/plugins/pdfparser-lib/pdfparser/src/Smalot/PdfParser/RawData/FilterHelper.php';

if (file_exists($autoload_path)) {
    require_once $autoload_path;
} else {
    error_log("ERREUR: Impossible de charger PDFParser - Fichier introuvable: " . $autoload_path);
}

if (file_exists($parser_path)) {
    require_once $parser_path;
} else {
    error_log("ERREUR : PDFParser introuvable !");
}

if (file_exists($tcpdf_path)) {
    require_once $tcpdf_path;
} else {
    error_log("ERREUR : TCPDF introuvable !");
}

use Smalot\PdfParser\Parser;

// Crée un formulaire d'upload de CV.

function cv_upload_form() {
    ob_start(); ?>
    <form action="" method="post" enctype="multipart/form-data">
        <input type="file" name="cv_pdf" accept="application/pdf" required>
        <button type="submit" name="upload_cv">Convertir en JSON</button>
    </form>
    <?php display_json_link(); ?>
    <?php
    return ob_get_clean();
	
}
add_shortcode('cv_to_json', 'cv_upload_form');

// Gère l'upload et la conversion du CV.

function handle_cv_upload() {
    if (isset($_POST['upload_cv']) && !empty($_FILES['cv_pdf']['tmp_name'])) {
        error_log("Fichier détecté !");

        $file = $_FILES['cv_pdf'];

        if ($file['type'] !== 'application/pdf') {
            error_log("Erreur : Format de fichier non valide !");
            wp_die("Erreur : Merci de télécharger un fichier PDF.");
        }

        // Déplacer le fichier temporaire vers le dossier WordPress
        $upload_dir = wp_upload_dir();
        $pdf_path = $upload_dir['path'] . '/' . basename($file['name']);
        
        if (!move_uploaded_file($file['tmp_name'], $pdf_path)) {
            error_log("Erreur : Impossible d'enregistrer le fichier.");
            wp_die("Erreur : Impossible d'enregistrer le fichier.");
        }

        error_log("PDF déplacé avec succès vers " . $pdf_path);

        // Conversion du PDF en texte
        try {
            error_log("Initialisation de PDFParser...");
            $parser = new Smalot\PdfParser\Parser();
            error_log("PDFParser instancié !");

            $pdf = $parser->parseFile($pdf_path);
            error_log("Extraction du texte...");
            $text = trim($pdf->getText());

            if (empty($text)) {
                error_log("Erreur : Le fichier PDF semble être vide ou illisible.");
                wp_die("Erreur : Le fichier PDF semble être vide ou illisible.");
            }

            error_log("Texte extrait : " . substr($text, 0, 200) . "..."); // Afficher un extrait

            // Création du JSON
            $json_data = [
                'nom' => '',
                'email' => '',
                'téléphone' => '',
                'expérience' => [],
                'compétences' => [],
                'texte_brut' => $text
            ];

			// $json_output = json_encode($json_data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
			
            // Détection des informations
            if (preg_match('/\b[A-Za-z]+\s[A-Za-z]+/', $text, $matches)) {
                $json_data['nom'] = trim($matches[0]);
            }
            if (preg_match('/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/', $text, $matches)) {
                $json_data['email'] = trim($matches[0]);
            }
            if (preg_match('/\+?\d{10,15}/', $text, $matches)) {
                $json_data['téléphone'] = trim($matches[0]);
            }

            // Sauvegarde du JSON sur le serveur
            $json_path = $upload_dir['path'] . '/' . pathinfo($file['name'], PATHINFO_FILENAME) . '.json';
            file_put_contents($json_path, json_encode($json_data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

            // Génération de l'URL du JSON
            $json_url = $upload_dir['url'] . '/' . basename($json_path);

            // Redirection après soumission
            wp_redirect(add_query_arg(['json_url' => urlencode($json_url)], home_url($_SERVER['REQUEST_URI'])));
            exit;

        } catch (Exception $e) {
            error_log("Erreur : " . $e->getMessage());
            wp_die("Erreur : " . $e->getMessage());
        }
    } else {
        error_log("Aucun fichier détecté !");
    }
}

// Exécuter `handle_cv_upload` uniquement à la soumission du formulaire
add_action('init', 'handle_cv_upload');

// Affichage du lien JSON après conversion

function display_json_link() {
    // Vérifier que l'URL JSON est présente et que le bouton n'a pas déjà été affiché
    if (isset($_GET['json_url']) && !did_action('display_json_link_rendered')) {
        do_action('display_json_link_rendered'); // Marquer comme affiché une fois

        echo '<div class="json-container">';
        echo '<h3 class="json-success">Conversion réussie !</h3>';
        echo '<p class="json-text">Téléchargez votre CV converti en JSON ici :</p>';
        echo '<a href="' . esc_url($_GET['json_url']) . '" download>';
        echo '<button class="json-button">Télécharger le JSON</button>';
        echo '</a>';
        echo '</div>';
    }
}
