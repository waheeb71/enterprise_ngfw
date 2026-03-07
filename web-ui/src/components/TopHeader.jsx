import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, Bell, User } from 'lucide-react';
import './TopHeader.css';

const TopHeader = () => {
    const { i18n, t } = useTranslation();

    const toggleLanguage = () => {
        const newLang = i18n.language === 'en' ? 'ar' : 'en';
        i18n.changeLanguage(newLang);
    };

    return (
        <header className="top-header glass-panel">
            <div className="header-search">
                <div className="search-box">
                    <input type="text" placeholder="Search IPs, Rules, Events..." className="search-input" />
                </div>
            </div>

            <div className="header-actions">
                <div className="ha-status">
                    <span className="ha-badge master">{t('ha_master')}</span>
                </div>

                <button className="action-btn" onClick={toggleLanguage} title={t('language')}>
                    <Globe size={20} />
                    <span className="lang-text">{i18n.language === 'en' ? 'عربي' : 'EN'}</span>
                </button>

                <button className="action-btn notification-btn">
                    <Bell size={20} />
                    <span className="notification-badge">3</span>
                </button>

                <div className="user-profile">
                    <div className="avatar">
                        <User size={20} />
                    </div>
                    <div className="user-info">
                        <span className="user-name">Admin</span>
                        <span className="user-role">Superuser</span>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default TopHeader;
