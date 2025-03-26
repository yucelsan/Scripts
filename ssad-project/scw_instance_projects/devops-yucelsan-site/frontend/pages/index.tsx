import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="w-full px-6 py-4 bg-white shadow-sm flex justify-between items-center">
        <h1 className="text-xl font-bold">SSAD YUCELSAN</h1>
        <nav className="space-x-4">
          <Link href="/login"><Button variant="ghost">Connexion</Button></Link>
          <Link href="/register"><Button>Inscription</Button></Link>
        </nav>
      </header>
      <main className="flex-grow flex flex-col items-center justify-center text-center p-10">
        <h2 className="text-4xl font-extrabold mb-4">Plateforme DevOps</h2>
        <p className="max-w-xl text-gray-600 mb-6">
          Créez vos environnements de développement ou de production en quelques clics.
        </p>
        <div className="space-x-4">
          <Link href="/register"><Button className="text-lg">Commencer</Button></Link>
          <Link href="/dashboard"><Button variant="outline" className="text-lg">Démo</Button></Link>
        </div>
      </main>
      <footer className="w-full bg-white text-center p-4 border-t text-sm text-gray-500">
        © {new Date().getFullYear()} YUCELSAN • Tous droits réservés
      </footer>
    </div>
  );
}