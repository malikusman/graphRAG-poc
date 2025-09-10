// MongoDB initialization script
db = db.getSiblingDB('sagewrite');

// Create collections
db.createCollection('documents');
db.createCollection('sections');
db.createCollection('entities');
db.createCollection('relationships');

// Create indexes for better performance
db.documents.createIndex({ "doi": 1 }, { unique: true });
db.documents.createIndex({ "title": "text", "abstract": "text" });
db.documents.createIndex({ "year": 1 });
db.documents.createIndex({ "status": 1 });

db.sections.createIndex({ "document_id": 1 });
db.sections.createIndex({ "section_type": 1 });
db.sections.createIndex({ "year": 1 });
// Vector index will be created later for embeddings

db.entities.createIndex({ "name": 1 });
db.entities.createIndex({ "type": 1 });
db.entities.createIndex({ "category": 1 });
db.entities.createIndex({ "frequency": -1 });

db.relationships.createIndex({ "source_entity": 1, "target_entity": 1 });
db.relationships.createIndex({ "type": 1 });
db.relationships.createIndex({ "strength": -1 });

// Create a user for the application
db.createUser({
  user: 'sagewrite_user',
  pwd: 'sagewrite_password',
  roles: [
    {
      role: 'readWrite',
      db: 'sagewrite'
    }
  ]
});

print('Database initialized successfully!');

