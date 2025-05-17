-- MySQL dump 10.13  Distrib 8.0.20, for Win64 (x86_64)
--
-- Host: 192.168.18.132    Database: password_manager
-- ------------------------------------------------------
-- Server version	5.5.5-10.11.6-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `credentials`
--

DROP TABLE IF EXISTS `credentials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `credentials` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `module` varchar(100) DEFAULT NULL,
  `ip` varchar(100) DEFAULT NULL,
  `port` varchar(10) DEFAULT NULL,
  `username` varchar(100) DEFAULT NULL,
  `password` text DEFAULT NULL,
  `note` text DEFAULT NULL,
  `url` varchar(255) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_module` (`module`),
  KEY `fk_user` (`user_id`),
  CONSTRAINT `fk_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `credentials`
--

LOCK TABLES `credentials` WRITE;
/*!40000 ALTER TABLE `credentials` DISABLE KEYS */;
INSERT INTO `credentials` VALUES (18,'editedtest','utyvuyt','vutvytww','tcytcytc','gAAAAABoJGDO_iH5ILb0VwjfSZoolXwmKISsgWnUw75SPiLBg7kWn6YxvnN-oD1lYnMHE6WZMGdMlV-cRu7OoZdkv9qhn6-fGw==','cycytc','tcytcy',1),(24,'sandiptcgdigital','ytcy','tvvut','tcytcytc','gAAAAABoJHLSckGaXw88bXVUKK1sZZrsvt6zZdqD97xueIkwC2aV4lRNj4l-8_vfJ5UyEbbRqcv_VD-hGw6u0ixcZWkVtGwfUw==','tyt','ycytcy',11),(25,'tcgdigital11111','bjhv11','jhvjv','mhvjhvj','gAAAAABoJHwMYahwYNcOe6b3CUoNJ7ZmUP6PcuMkMf25gCvvYeWdhBGHO7ACqtQoeP9QKBdajl_PXvNIwXOVLkNqORQeJufq0w==','','jhvjvj',11),(27,'sandip','1234','chtct','tcutcut','gAAAAABoJGNsy-pQlNggOvFvsfyzLXjrxRvrqdOXMESSjop7FTSujq2-CjsGK_ClfxaylgmEOrt2tb0mrUyxCuZuC6lS0rfCRQ==','ytcytv','utcytc',11);
/*!40000 ALTER TABLE `credentials` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_module_access`
--

DROP TABLE IF EXISTS `user_module_access`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_module_access` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `module` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`module`),
  CONSTRAINT `user_module_access_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_module_access`
--

LOCK TABLES `user_module_access` WRITE;
/*!40000 ALTER TABLE `user_module_access` DISABLE KEYS */;
INSERT INTO `user_module_access` VALUES (27,2,'sandiptcgdigital'),(26,2,'tcgdigital11111'),(28,12,'sandiptcgdigital');
/*!40000 ALTER TABLE `user_module_access` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `password_hash` text NOT NULL,
  `role` enum('user','admin') NOT NULL DEFAULT 'user',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin','scrypt:32768:8:1$cJ7qxOaoxmUYc7zb$7883972ddff9396807db91a95bbb3d9653aa4d591771a30b31d102912297cc558b83f8f50e1364df22b205fa9ad8fdc721defb3c4a7a478264ee5d27c15ed2a1','admin'),(2,'dev','scrypt:32768:8:1$jv123eeXNnt7yCAC$a60cf4db0ed396587733d0893a45a7f2c3164e885161e85d3820138d382cca4e2efc74369cf260531894d52c71b5dc94adb0307ce63d6d1bd55b929bbe377d02','user'),(8,'admin1','scrypt:32768:8:1$YnQqTK9K1WLAvQ7j$02fbf26ff9876d2f62c6fe293b0e5c04ec3a31be06ecc1c7e06995415fe4910e63cd11e79837365b8c1b8b960cb4ec9e685a063df17764cada72db57c77e1ce5','admin'),(11,'tcgdigital','scrypt:32768:8:1$T9al83vugPEs1Zy7$42328e7ac8689beb07a045e5010e8357a34990f6af2a0b9730829c688ec5fef2c600e3d63e30bead2d9d2ac4e376941c33c46367fcdb077097eb40d421eac199','user'),(12,'sandip','scrypt:32768:8:1$DW5Jql2mTIzOjlyZ$b1873b252eeaeccdc042636ccdde6bb28a51ca83338c35c3311b7b09222249207740a0f4246f2929de5f3836ad51009164abdfc27e5f86b9f9021cdb021066d8','user');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'password_manager'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-05-14 17:35:58
